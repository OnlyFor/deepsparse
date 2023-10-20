from deepsparse.v2.operators import EngineOperator, Operator
from deepsparse import Context as EngineContext
from typing import Any 
from deepsparse.v2.utils import Context
from pydantic import BaseModel, Field
from deepsparse.utils.onnx import CACHE_INPUT_PREFIX,

__all__ = ["NLEngineOperator"]

class NlEngineInput(BaseModel):
    inputs: Any = Field(description="engine inputs")
    kv_cache: DecoderKVCache = Field(description="kv_cache object")


class NLEngineOperator(EngineOperator):
    input_schema = NlEngineInput
    output_schema = None

    def __init__(self,
            sequence_length: int, 
            input_ids_length: int,
            enable_multitoken_prefill: bool,
            internal_kv_cache: bool = False,
            **kwargs):

        (
            onnx_file_path,
            output_indices_to_be_cached,
            kv_cache_data_type,
        ) = overwrite_onnx_model_inputs_for_kv_cache_models(
            onnx_file_path=kwargs.get("model_path"),
            batch_size=kwargs.get("batch_size", 1),
            sequence_length=sequence_length,
            input_ids_length=input_ids_length,
        )

        self._can_operate = enable_multitoken_prefill
        self.kv_cache_data_type = None
        if any(output_indices_to_be_cached):
            self.kv_cache_data_type = kv_cache_data_type
            if internal_kv_cache and kwargs.get("engine_type") == DEEPSPARSE_ENGINE:
                # inform the engine, that are using the kv cache
                engine_kwargs = kwargs.get("engine_kwargs")
                if not engine_kwargs:
                    engine_kwargs = {}
                engine_kwargs["cached_outputs"] = output_indices_to_be_cached

        kwargs["engine_kwargs"] = engine_kwargs 
        kwargs["model_path"] = onnx_file_path
        super().__init__(**kwargs)

        self.sequence_length = sequence_length
        self.input_ids_length = input_ids_length

    @property
    def can_operate(self):
        return self._can_operate

    def run(self, inp: NlEngineInput, context: Optional[Context]) -> Any:
        engine_input = inp.inputs
        kv_cache = inp.kv_cache

        inputs = self._add_kv_cache_to_input(engine_input, kv_cache)
        if bool(kv_cache.engine_internal_cache):
            # conventionally, before dispatching
            # inputs to the engine, we validate them
            # if val_inp=True. However, in this case
            # we want to pass the empty kv cache inputs
            # (batch_size=0) to the engine. Therefore,
            # we skip the validation
            out = self.engine._eng_net.execute_list_out(
                inputs, kv_cache.engine_internal_cache
            )
        else:
            # run the engine without the LIB.kv_cache object
            out = super().__call__(inputs)
            
        logits, *kv_cache_state = out
        self._update_kv_cache(
            kv_cache_state=kv_cache_state,
            input_ids_len=self.input_ids_length,
            kv_cache=kv_cache,
        )
        return logits

    def _add_kv_cache_to_input(self, engine_input, kv_cache):
        kv_cache_state = copy.copy(kv_cache.cached_inputs)

        for idx, input_name in enumerate(self.onnx_input_names_no_cache):
            kv_cache_state[input_name] = inp[idx]

        new_inp = [kv_cache_state[name] for name in self.engine.input_names]
        return new_inp
    
    def _update_kv_cache(self, kv_cache_state, input_ids_len, kv_cache):
        if bool(kv_cache.engine_internal_cache):
            kv_cache.total_num_processed_tokens += input_ids_len
            return

        kv_cache_state = {
            name: array
            for name, array in zip(self.onnx_input_names_cached, kv_cache_state)
        }

        kv_cache.update(
            state=kv_cache_state,
            input_ids_len=input_ids_len,
        )

    @property
    def onnx_input_names_no_cache(self) -> List[str]:
        """
        :return: The input names for the onnx model, excluding
            the potential kv cache inputs
        """
        return [
            name
            for name in self.engine.input_names
            if not name.startswith(CACHE_INPUT_PREFIX)
        ]

    @property
    def onnx_input_names_cached(self) -> List[str]:
        """
        :return: The cached input names for the onnx model
        """
        return [
            name
            for name in self.engine.input_names
            if name.startswith(CACHE_INPUT_PREFIX)
        ]

    @property
    def cache_shape(self) -> Tuple[int, int, int, int]:
        """
        :return: The shape of the kv cache inputs
            for the onnx model. The shape is
            (batch_size, num_heads, sequence_length, hidden_size)
        """
        cache_engine_input_index = next(
            i
            for i, name in enumerate(self.engine.input_names)
            if CACHE_INPUT_PREFIX in name
        )
        return self.engine.input_shapes[cache_engine_input_index]

    @property
    def output_names(self) -> List[str]:
        """
        :return: The output names for the onnx model
        """
        return self.engine.output_names
    
    
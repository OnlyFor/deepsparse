# Copyright (c) 2021 - present / Neuralmagic, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from typing import Any
from pydantic import BaseModel, Field

from deepsparse.v2.operators import Operator
from deepsparse.v2.utils import InferenceState, PipelineState
from deepsparse.v2.text_generation.prep_for_prefill import PrepareforPrefillOutput


__all__ = ["CompilePromptLogits"]

class PrepareforPrefillOutput(BaseModel):
    tokens: list = Field(description="tokens")
    kv_cache: Any = Field(description="KV Cache") #DecoderKVCache

class CompilePromptLogits(Operator):
    output_schema = PrepareforPrefillOutput

    def run(
        self, inp: Any, pipeline_state: PipelineState, inference_state: InferenceState
    ):
        logit_type = "prompt_logits"
        logits = inp.get("logits")

        if inference_state.current_state.get(logit_type):
            current_logits = inference_state.current_state.get(logit_type).copy()
            current_logits.extend(logits)
        else:
            current_logits = logits

        state_update = dict(logit_type=current_logits)
        return {"kv_cache": inp.kv_cache, "tokens": inp.tokens}, state_update

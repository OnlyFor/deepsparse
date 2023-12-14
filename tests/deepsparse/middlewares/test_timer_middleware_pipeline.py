# Copyright (c) 2021 - present / Neuralmagic, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by call_nextlicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

from collections import defaultdict
from typing import List

from deepsparse.middlewares import MiddlewareManager, MiddlewareSpec, TimerMiddleware
from deepsparse.pipeline import Pipeline
from deepsparse.routers import LinearRouter
from deepsparse.schedulers import ContinuousBatchingScheduler, OperatorScheduler
from tests.deepsparse.middlewares import PrintingMiddleware, SendStateMiddleware
from tests.deepsparse.pipelines.test_basic_pipeline import (
    AddOneOperator,
    AddTwoOperator,
    IntSchema,
)


def test_timer_middleware_timings_saved_in_timer_manager():
    """Check runtimes from timer manager saved into timer_manager"""

    middlewares = [
        MiddlewareSpec(PrintingMiddleware),  # debugging
        MiddlewareSpec(SendStateMiddleware),  # for callable entry and exit order
        MiddlewareSpec(TimerMiddleware),  # for timer
    ]

    ops = [AddOneOperator(), AddTwoOperator()]

    AddThreePipeline = Pipeline(
        ops=ops,
        router=LinearRouter(end_route=2),
        schedulers=[OperatorScheduler()],
        continuous_batching_scheduler=ContinuousBatchingScheduler,
        middleware_manager=MiddlewareManager(middlewares),
    )

    pipeline_input = IntSchema(value=5)
    pipeline_output = AddThreePipeline(pipeline_input)
    assert pipeline_output.value == 8

    pipeline_measurements: List[
        defaultdict
    ] = AddThreePipeline.timer_manager.measurements
    measurements = pipeline_measurements[0]

    # Pipeline, AddOneOperator, AddTwoOperator should have one measurement each
    assert len(measurements) == 3

    # assert pipeline time is more than the sum of two ops
    pipeline_time: List[float] = measurements["total"]
    add_one_operator_time, add_two_operator_time = (
        measurements["AddOneOperator"],
        measurements["AddTwoOperator"],
    )

    assert pipeline_time > add_one_operator_time + add_two_operator_time

    # check middleware triggered for Pipeline and Ops as expected
    state = AddThreePipeline.middleware_manager.state
    assert "SendStateMiddleware" in state

    # three measurements, two operators + one pipeline
    assert len(measurements) == len(ops) + 1

    # SendStateMiddleware, order of calls:
    # Pipeline start, AddOneOperator start, AddOneOperator end
    # AddTwoOperator start, AddTwoOperator end, Pipeline end
    expected_order = [0, 0, 1, 0, 1, 1]
    assert state["SendStateMiddleware"] == expected_order

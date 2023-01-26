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
"""
The set of the general built-in metric functions
"""
from typing import Any, List, Union


__all__ = ["identity"]


def identity(x: Any):
    """
    Simple identity function

    :param x: Any object
    :return: The same object
    """
    return x

def all_predicted_classes(classes: List[Union[int, str, List[int], List[str]]]):
    if list[0]



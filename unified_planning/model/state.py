# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import Dict, List, Optional
import unified_planning as up
from unified_planning.exceptions import UPUsageError, UPValueError


class ROState:
    '''This is an abstract class representing a classical Read Only state'''

    def get_value(self, value: 'up.model.FNode') -> 'up.model.FNode':
        '''
        This method retrieves the value in the state.
        NOTE that the searched value must be set in the state.
        :params value: The value searched for in the state.
        :return: The set value.
        '''
        raise NotImplementedError


class RWState(ROState):
    '''This is an abstract class representing a classical Read/Write state'''

    def set_values(self, new_values: Dict['up.model.FNode', 'up.model.FNode']) -> 'RWState':
        '''
        Returns a different UPRWState in which every value in new_values.keys() is evaluated as his mapping
        in new the new_values dict and every other value is evaluated as in self.
        :param new_values: The dictionary that contains the values that need to be updated in the new State.
        :return: The new State created.
        '''
        raise NotImplementedError


class UPRWState(RWState):
    '''
    unified_planning implementation of the RWState interface.
    This class has a field "MAX_ANCESTORS" set to 20.

    The higher this numer is, the less memory the data structure will use.
    The lower this number is, the less time the data structure will need to retrieve a value.

    To set your own number just extend this class and re-define the MAX_ANCESTORS value. It must be > 0
    '''
    MAX_ANCESTORS: int = 20
    '''This class is the unified_planning implementation of the RWState interface.'''
    def __init__(self, values: Dict['up.model.FNode', 'up.model.FNode'], father: Optional['UPRWState'] = None):
        if type(self).MAX_ANCESTORS < 1:
            raise UPValueError(f'The max_ancestor field of a class extending UPRWState must be > 0: in the class {type(self)} it is set to {type(self).MAX_ANCESTORS}')
        self._father = father
        self._values = values
        if father is None:
            self._ancestors = 0
        else:
            self._ancestors = father._ancestors + 1

    def __repr__(self) -> str:
        current_instance = self
        retval = ''
        while current_instance is not None:
            retval = f'{retval}\n{str(current_instance._values)}'
            current_instance = current_instance._father # type: ignore
        return retval

    def _has_value(self, value: 'up.model.FNode') -> bool:
        '''
        Method for internal use only.
        This method returns True if the parameter value is in this specific instance;
        NOTE that if self._has_value(x) returns False does not mean that self.get_value(x) will not retrieve any value.
        :param value: The value searched in this instance of the class.
        :return: True if this instance holds the value, False otherwise.
        '''
        return value in self._values

    def get_value(self, value: 'up.model.FNode') -> 'up.model.FNode':
        '''
        This method retrieves the value in the state.
        NOTE that the searched value must be set in the state.
        :params value: The value searched for in the state.
        :return: The set value.
        '''
        right_instance: Optional[UPRWState] = self
        while right_instance is not None:
            if right_instance._has_value(value):
                return right_instance._values[value]
            else:
                right_instance = right_instance._father
        raise UPUsageError(f'The state {self} does not have a value for the value {value}')

    def set_values(self, new_values: Dict['up.model.FNode', 'up.model.FNode']) -> 'UPRWState':
        '''
        Returns a different UPRWState in which every value in new_values.keys() is evaluated as his mapping
        in new the new_values dict and every other value is evaluated as in self.
        :param new_values: The dictionary that contains the values that need to be updated in the new State.
        :return: The new State created.
        '''
        # If the number of ancestors is less that the given threshold it just creates a new state with self set as the father.
        if self._ancestors < type(self).MAX_ANCESTORS:
            return UPRWState(new_values, self)
        # Otherwise we retrieve every ancestor, and from the oldest to the newest we update the "complete_values" dict
        else:
            current_element: Optional[UPRWState] = self
            complete_values = new_values.copy()
            while current_element is not None:
                for k, v in current_element._values.items():
                    complete_values.setdefault(k, v)
                current_element = current_element._father
            return UPRWState(complete_values)

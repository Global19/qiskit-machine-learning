# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

""" Test Opflow QNN """

from typing import List

from test import QiskitMachineLearningTestCase

import unittest
from ddt import ddt, data

import numpy as np
from qiskit.providers.aer import QasmSimulator, StatevectorSimulator
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.opflow import PauliExpectation, Gradient, StateFn, PauliSumOp, ListOp
from qiskit.utils import QuantumInstance


from qiskit_machine_learning.neural_networks import OpflowQNN


@ddt
class TestOpflowQNN(QiskitMachineLearningTestCase):
    """Opflow QNN Tests."""

    def setUp(self):
        super().setUp()

        # specify quantum instances
        self.sv_quantum_instance = QuantumInstance(StatevectorSimulator())
        self.qasm_quantum_instance = QuantumInstance(QasmSimulator(shots=100))

    def validate_output_shape(self, qnn: OpflowQNN, test_data: List[np.ndarray]) -> None:
        """
        Asserts that the opflow qnn returns results of the correct output shape.

        Args:
            qnn: QNN to be tested
            test_data: list of test input arrays

        Raises:
            QiskitMachineLearningError: Invalid input.
        """

        # get weights
        weights = np.random.rand(qnn.num_weights)

        # iterate over test data and validate behavior of model
        for x in test_data:

            # evaluate network
            forward_shape = qnn.forward(x, weights).shape
            grad = qnn.backward(x, weights)
            backward_shape_input = grad[0].shape
            backward_shape_weights = grad[1].shape

            # derive batch shape form input
            batch_shape = x.shape[:-len(qnn.output_shape)]
            if len(batch_shape) == 0:
                batch_shape = (1,)

            # compare results and assert that the behavior is equal
            self.assertEqual(forward_shape, (*batch_shape, *qnn.output_shape))
            self.assertEqual(backward_shape_input,
                             (*batch_shape, *qnn.output_shape, qnn.num_inputs))
            self.assertEqual(backward_shape_weights,
                             (*batch_shape, *qnn.output_shape, qnn.num_weights))

    @data(
        'sv', 'qasm'
    )
    def test_opflow_qnn_1_1(self, q_i):
        """ Test Opflow QNN with input/output dimension 1/1."""

        if q_i == 'sv':
            quantum_instance = self.sv_quantum_instance
        else:
            quantum_instance = self.qasm_quantum_instance

        # specify how to evaluate expected values and gradients
        expval = PauliExpectation()
        gradient = Gradient()

        # construct parametrized circuit
        params = [Parameter('input1'), Parameter('weight1')]
        qc = QuantumCircuit(1)
        qc.h(0)
        qc.ry(params[0], 0)
        qc.rx(params[1], 0)
        qc_sfn = StateFn(qc)

        # construct cost operator
        cost_operator = StateFn(PauliSumOp.from_list([('Z', 1.0), ('X', 1.0)]))

        # combine operator and circuit to objective function
        op = ~cost_operator @ qc_sfn

        # define QNN
        qnn = OpflowQNN(op, [params[0]], [params[1]],
                        expval, gradient, quantum_instance=quantum_instance)

        test_data = [
            np.array(1),
            np.array([1]),
            np.array([[1], [2]]),
            np.array([[[1], [2]], [[3], [4]]])
        ]

        # test model
        self.validate_output_shape(qnn, test_data)

    @data(
        'sv', 'qasm'
    )
    def test_opflow_qnn_2_1(self, q_i):
        """ Test Opflow QNN with input/output dimension 2/1."""

        # construct QNN
        if q_i == 'sv':
            quantum_instance = self.sv_quantum_instance
        else:
            quantum_instance = self.qasm_quantum_instance

        # specify how to evaluate expected values and gradients
        expval = PauliExpectation()
        gradient = Gradient()

        # construct parametrized circuit
        params = [Parameter('input1'), Parameter('input2'),
                  Parameter('weight1'), Parameter('weight2')]
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.ry(params[0], 0)
        qc.ry(params[1], 1)
        qc.rx(params[2], 0)
        qc.rx(params[3], 1)
        qc_sfn = StateFn(qc)

        # construct cost operator
        cost_operator = StateFn(PauliSumOp.from_list([('ZZ', 1.0), ('XX', 1.0)]))

        # combine operator and circuit to objective function
        op = ~cost_operator @ qc_sfn

        # define QNN
        qnn = OpflowQNN(op, params[:2], params[2:],
                        expval, gradient, quantum_instance=quantum_instance)

        test_data = [
            np.array([1, 2]),
            np.array([[1, 2]]),
            np.array([[1, 2], [3, 4]])
        ]

        # test model
        self.validate_output_shape(qnn, test_data)

    @data(
        'sv', 'qasm'
    )
    def test_opflow_qnn_2_2(self, q_i):
        """ Test Opflow QNN with input/output dimension 2/2."""

        if q_i == 'sv':
            quantum_instance = self.sv_quantum_instance
        else:
            quantum_instance = self.qasm_quantum_instance

        # construct parametrized circuit
        params_1 = [Parameter('input1'), Parameter('weight1')]
        qc_1 = QuantumCircuit(1)
        qc_1.h(0)
        qc_1.ry(params_1[0], 0)
        qc_1.rx(params_1[1], 0)
        qc_sfn_1 = StateFn(qc_1)

        # construct cost operator
        h_1 = StateFn(PauliSumOp.from_list([('Z', 1.0), ('X', 1.0)]))

        # combine operator and circuit to objective function
        op_1 = ~h_1 @ qc_sfn_1

        # construct parametrized circuit
        params_2 = [Parameter('input2'), Parameter('weight2')]
        qc_2 = QuantumCircuit(1)
        qc_2.h(0)
        qc_2.ry(params_2[0], 0)
        qc_2.rx(params_2[1], 0)
        qc_sfn_2 = StateFn(qc_2)

        # construct cost operator
        h_2 = StateFn(PauliSumOp.from_list([('Z', 1.0), ('X', 1.0)]))

        # combine operator and circuit to objective function
        op_2 = ~h_2 @ qc_sfn_2

        op = ListOp([op_1, op_2])

        qnn = OpflowQNN(op, [params_1[0], params_2[0]], [params_1[1], params_2[1]],
                        quantum_instance=quantum_instance)

        test_data = [
            np.array([1, 2]),
            np.array([[1, 2], [3, 4]])
        ]

        # test model
        self.validate_output_shape(qnn, test_data)


if __name__ == '__main__':
    unittest.main()

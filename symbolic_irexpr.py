#!/usr/bin/env python
'''This module handles constraint generation.'''

import z3
import pyvex
import symbolic
import symbolic_irop
import random

import logging
l = logging.getLogger("symbolic_irexpr")
l.setLevel(logging.DEBUG)

###########################
### Expression handlers ###
###########################
def handle_get(expr, state):
	# TODO: proper SSO registers
	if expr.offset not in state.registers:
		# TODO: handle register partials (ie, ax) as symbolic pieces of the full register
		state.registers[expr.offset] = [ z3.BitVec("reg_%d_%d" % (expr.offset, 0), symbolic.get_size(expr.type)) ]
	return state.registers[expr.offset][-1]

def handle_op(expr, state):
	args = expr.args()
	return symbolic_irop.translate(expr.op, args, state)

def handle_rdtmp(expr, state):
	return state.temps[expr.tmp]

def handle_const(expr, state):
	size = symbolic.get_size(expr.con.type)
	t = type(expr.con.value)
	if t == int or t == long:
		return z3.BitVecVal(expr.con.value, size)
	raise Exception("Unsupported constant type: %s" % type(expr.con.value))

def handle_load(expr, state):
	# TODO: symbolic memory
	size = symbolic.get_size(expr.type)
	l.debug("Load of size %d" % size)
	m_id = random.randint(0, 100)
	l.debug("... ID: %d" % m_id)
	m = z3.BitVec("tmp_memory_%d" % m_id, size)
	return m

def handle_ccall(expr, state):
	if expr.callee.name == "amd64g_calculate_condition":
		# TODO: placeholder
		return translate(expr.args()[0], state) | translate(expr.args()[1], state)
	raise Exception("Unsupported callee %s" % expr.callee.name)

expr_handlers = { }
expr_handlers[pyvex.IRExpr.Get] = handle_get
expr_handlers[pyvex.IRExpr.Unop] = handle_op
expr_handlers[pyvex.IRExpr.Binop] = handle_op
expr_handlers[pyvex.IRExpr.Triop] = handle_op
expr_handlers[pyvex.IRExpr.Qop] = handle_op
expr_handlers[pyvex.IRExpr.RdTmp] = handle_rdtmp
expr_handlers[pyvex.IRExpr.Const] = handle_const
expr_handlers[pyvex.IRExpr.Load] = handle_load
expr_handlers[pyvex.IRExpr.CCall] = handle_ccall

def translate(expr, state):
	t = type(expr)
	if t not in expr_handlers:
		raise Exception("Unsupported expression type %s." % str(t))
	l.debug("Handling IRExpr %s" % t)
	return expr_handlers[t](expr, state)
from __future__ import print_function
from ortools.linear_solver import pywraplp

# Tutorial is available at: https://developers.google.com/optimization/introduction/python
def main():
  solver = pywraplp.Solver('SolveSimpleSystem',
                           pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
  x = solver.NumVar(0, 1, 'x')
  y = solver.NumVar(0, 2, 'y')
  # Constraint 1: y - x >= 2.
  constraint1 = solver.Constraint(2, solver.infinity())
  constraint1.SetCoefficient(x, -1)
  constraint1.SetCoefficient(y, 1)
  # Objective is max: x + y
  objective = solver.Objective()
  objective.SetCoefficient(x, 1)
  objective.SetCoefficient(y, 1)
  objective.SetMaximization()
  solver.Solve()
  print('Solution:')
  print('x = ', x.solution_value())
  print('y = ', y.solution_value())

if __name__ == '__main__':
  main()

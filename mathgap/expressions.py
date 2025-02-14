from typing import Any, List
import numpy as np

from pydantic import BaseModel, Field


class Expr(BaseModel):
    # memoize results (especially important if many subexpressions are evaluated)
    is_cache_enabled: bool = Field(default=False)

    def __init__(self, subexpressions: List['Expr'] = None, **data) -> None:
        super().__init__(**data)
        self._subexpressions = [] if subexpressions is None else subexpressions
        self._cached_eval = None
        self._cached_grad = None

    def eval(self, instantiation):
        """ 
            Evaluates this expression recursively 
            - instantiation: assigning values to variables
        """
        if self.is_cache_enabled:
            if self._cached_eval is None:
                self._cached_eval = self._eval(instantiation)
            return self._cached_eval
        else:
            return self._eval(instantiation)

    def _eval(self, instantiation):
        ...
    
    def grad(self, wrt_vars: List[Any], instantiation):
        """
            Computes the gradient of this expression with respect to a list of variables
            under a given instantiation.

            - wrt_vars: the variable identifiers with respect to which the gradient should be computed
            - instantiation: instantiation of the variables
            - allow_cache: whether or not the result should be cached for subsequent re-use
                NOTE: you are then responsible for consistency (e.g. clearing cache if numbers change etc)
        """
        if self.is_cache_enabled:
            if self._cached_grad is None:
                self._cached_grad = self._grad(wrt_vars, instantiation)
            return self._cached_grad
        else:
            return self._grad(wrt_vars, instantiation)

    def _grad(self, wrt_vars: List[Any], instantiation, allow_cache: bool = False):
        ...

    def enable_cache(self, recursive: bool = True):
        """ 
            Enables memoization of values
            NOTE: you will be in charge of ensuring consistency (e.g. clearing the cache if the instantiation changes)
        """
        self.is_cache_enabled = True
        if recursive:
            for s in self._subexpressions:
                s.enable_cache(recursive)

    def disable_cache(self, recursive: bool = True):
        self.is_cache_enabled = False
        if recursive:
            for s in self._subexpressions:
                s.disable_cache(recursive)

    def clear_cache(self, recursive: bool = True):
        self._cached_eval = None
        self._cached_grad = None
        if recursive:
            for s in self._subexpressions:
                s.clear_cache(recursive)
    
    def to_str(self, instantiation, depth: int, with_parentheses: bool = True) -> str:
        """ 
            Converts the expression into a string, where everything will be evaluated beyond depth.
            E.g. to_str((num1 + num2) + num3, {num1: 3, num2: 7, num3: 5}, depth=1) -> "10 + 3"

            - instantiation: the concrete values for each variable
            - depth: beyond which depth should values be evaluated instead of being printed as expressions¨
            - with_parentheses: should all subexpressions be put into parentheses (to avoid incorrectness)
        """
        ...

    def __str__(self) -> str:
        ...

class Const(Expr):
    value: Any

    def __init__(self, value: Any) -> None:
        super().__init__(subexpressions=None, value=value)

    def _eval(self, instantiation):
        return self.value

    def _grad(self, wrt_vars: List[Any], instantiation):
        return np.zeros(shape=(len(wrt_vars)))

    def to_str(self, instantiation, depth: int, with_parentheses: bool = True) -> str:
        return str(self.eval(instantiation))

    def __str__(self) -> str:
        return str(self.value)

class Variable(Expr):
    identifier: Any

    def __init__(self, identifier: Any) -> None:
        super().__init__(subexpressions=None, identifier=identifier)

    def _eval(self, instantiation):
        return instantiation._instantiations[self.identifier]

    def _grad(self, wrt_vars: List[Any], instantiation):
        return np.array(list(map(lambda x: 1.0 * (x == self.identifier), wrt_vars)))
    
    def to_str(self, instantiation, depth: int, with_parentheses: bool = True) -> str:
        return str(self.eval(instantiation))

    def __str__(self) -> str:
        return str(self.identifier)
    
class Sum(Expr):
    summands: List[Expr]

    def __init__(self, summands: List[Expr]) -> None:
        super().__init__(subexpressions=summands, summands=summands)

    def _eval(self, instantiation):
        return sum([a.eval(instantiation) for a in self.summands])

    def _grad(self, wrt_vars: List[Any], instantiation):
        return sum([s.grad(wrt_vars, instantiation) for s in self.summands])

    def to_str(self, instantiation, depth: int, with_parentheses: bool = True) -> str:
        if depth > 0:
            summands_str = [a.to_str(instantiation, depth=depth-1, with_parentheses=with_parentheses) for a in self.summands]
            if with_parentheses:
                return " + ".join([f"({a})" for a in summands_str])
            else:
                return " + ".join([f"{a}" for a in summands_str])
        else:
            return str(self.eval(instantiation))
    
    def __str__(self) -> str:
        return " + ".join([f"({str(a)})" for a in self.summands])
    
class Addition(Sum):
    def __init__(self, summand1: Expr, summand2: Expr) -> None:
        super().__init__(summands=[summand1, summand2])

class Subtraction(Expr):
    minuend: Expr
    subtrahend: Expr

    def __init__(self, minuend: Expr, subtrahend: Expr) -> None:
        super().__init__(subexpressions=[minuend, subtrahend], minuend=minuend, subtrahend=subtrahend)

    def _eval(self, instantiation):
        return self.minuend.eval(instantiation) - self.subtrahend.eval(instantiation)

    def _grad(self, wrt_vars: List[Any], instantiation):
        return self.minuend.grad(wrt_vars, instantiation) - self.subtrahend.grad(wrt_vars, instantiation)

    def to_str(self, instantiation, depth: int, with_parentheses: bool = True) -> str:
        if depth > 0:
            minuend_str = self.minuend.to_str(instantiation, depth=depth-1, with_parentheses=with_parentheses)
            subtrahend_str = self.subtrahend.to_str(instantiation, depth=depth-1, with_parentheses=with_parentheses)
            if with_parentheses:
                return f"({minuend_str}) - ({subtrahend_str})"
            else:
                return f"{minuend_str} - {subtrahend_str}"
        else:
            return str(self.eval(instantiation))

    def __str__(self) -> str:
        return f"({str(self.minuend)}) - ({str(self.subtrahend)})"
    
class Product(Expr):
    factor1: Expr
    factor2: Expr

    def __init__(self, factor1: Expr, factor2: Expr) -> None:
        super().__init__(subexpressions=[factor1, factor2], factor1=factor1, factor2=factor2)
        self.factor1 = factor1
        self.factor2 = factor2

    def _eval(self, instantiation):
        return self.factor1.eval(instantiation) * self.factor2.eval(instantiation)

    def _grad(self, wrt_vars: List[Any], instantiation):
        return self.factor2.eval(instantiation) * self.factor1.grad(wrt_vars, instantiation) \
             + self.factor1.eval(instantiation) * self.factor2.grad(wrt_vars, instantiation)

    def to_str(self, instantiation, depth: int, with_parentheses: bool = True) -> str:
        if depth > 0:
            factor1_str = self.factor1.to_str(instantiation, depth=depth-1, with_parentheses=with_parentheses)
            factor2_str = self.factor2.to_str(instantiation, depth=depth-1, with_parentheses=with_parentheses)
            if with_parentheses:
                return f"({factor1_str}) * ({factor2_str})"
            else:
                return f"{factor1_str} * {factor2_str}"
        else:
            return str(self.eval(instantiation))

    def __str__(self) -> str:
        return f"({str(self.factor1)}) * ({str(self.factor2)})"

class Fraction(Expr):
    numerator: Expr
    denominator: Expr

    def __init__(self, numerator: Expr, denominator: Expr) -> None:
        super().__init__(subexpressions=[numerator, denominator], numerator=numerator, denominator=denominator)
        self.numerator = numerator
        self.denominator = denominator

    def _eval(self, instantiation):
        return self.numerator.eval(instantiation) / self.denominator.eval(instantiation)
    
    def _grad(self, wrt_vars: List[Any], instantiation):
        dval = self.denominator.eval(instantiation)
        return 1.0 / dval * self.numerator.grad(wrt_vars, instantiation) \
             - self.numerator.eval(instantiation) / (dval**2) * self.denominator.grad(wrt_vars, instantiation)

    def to_str(self, instantiation, depth: int, with_parentheses: bool = True) -> str:
        if depth > 0:
            numerator_str = self.numerator.to_str(instantiation, depth=depth-1, with_parentheses=with_parentheses)
            denominator_str = self.denominator.to_str(instantiation, depth=depth-1, with_parentheses=with_parentheses)
            if with_parentheses:
                return f"({numerator_str}) / ({denominator_str})"
            else:
                return f"{numerator_str} / {denominator_str}"
        else:
            return str(self.eval(instantiation))

    def __str__(self) -> str:
        return f"({str(self.numerator)}) / ({str(self.denominator)})"
# Standard Python packages
import math
import numbers

# Special dependencies
import numpy

class InfiniteType:
    def __init__(self, multiplier=1.):
        if multiplier == 0.: raise ZeroDivisionError, "Cannot multiply infinity and zero."
        self._multiplier = multiplier

    def __repr__(self):
        if self is Infinity:
            return "Infinity"
        elif self is MinusInfinity:
            return "-Infinity"
        elif self._multiplier > 0.:
            return "Infinity*%g" % self._multiplier
        else:
            return "-Infinity*%g" % abs(self._multiplier)

    def __neg__(self):
        if self is Infinity:
            return MinusInfinity
        elif self is MinusInfinity:
            return Infinity
        else:
            return self * -1.

    def __mul__(self, number):
        if number == 0.: raise ZeroDivisionError, "Cannot multiply infinity and zero."
        return InfiniteType(self._multiplier * number)

    def __div__(self, number):
        if isinstance(number, InfiniteType): raise ZeroDivisionError, "Cannot divide infinity and infinity."
        if number == 0: raise ZeroDivisionError, "Cannot divide infinity and zero."
        return InfiniteType(self._multiplier / number)

    def __truediv__(self, number):
        return self.__div__(number)

#: Symbol representing infinity; can be multiplied by any scalar.
#:
#: Note: in a product, Infinity must *precede* the scalar::
#:
#:    >>> Infinity * -5.     # right
#:    >>> -5. * Infinity     # wrong
Infinity = InfiniteType()
MinusInfinity = InfiniteType(-1.)

#: A small number (1e-5), used to avoid numerical round-off issues in
#: comparisons.
#:
#: The following can be used to set epsilon (without any
#: multiple-reference issues)::
#: 
#:    >>> import cassius
#:    >>> cassius.epsilon = 1e-10
epsilon = 1e-5

######################################################### Utility functions

def _roundlevel_nsigfigs(num, n):
  if num == 0.: return 1
  return n - int(math.ceil(math.log10(abs(num))))

def str_round(num, n):
  """Round a number to n digits and return the result as a string."""
  num = round(num, n)
  format = "%."+str(max(n, 0))+"f"
  return format % num

def round_sigfigs(num, n):
  "Round a number to n significant figures."
  return round(num, _roundlevel_nsigfigs(num, n))

def str_sigfigs(num, n):
  """Round a number to n significant figures and return the result as
a string."""
  level = _roundlevel_nsigfigs(num, n)
  num = round(num, level)
  format = "%."+str(max(level, 0))+"f"
  return format % num

def round_errpair(num, err, n=2):
  """Round a number and its uncertainty to n significant figures in
  the uncertainty (default is two)."""

  level = _roundlevel_nsigfigs(err, n)
  return round(num, level), round(err, level)

def str_errpair(num, err, n=2):
  """Round a number and its uncertainty to n significant figures in the
uncertainty (default is two) and return the result as a string."""
  level = _roundlevel_nsigfigs(err, n)
  num = round(num, level)
  err = round(err, level)
  format = "%."+str(max(level, 0))+"f"
  return format % num, format % err

def unicode_errpair(num, err, n=2):
  """Round a number and its uncertainty to n significant figures in the
uncertainty (default is two) and return the result joined by a unicode
plus-minus sign."""
  output = u"\u00b1".join(str_errpair(num, err, n))
  return output.replace("-", u"\u2212")

def mean(*values, **kwds):
    """Compute the mean of N values (N > 0).

    Keyword arguments:
       decimals (int or `None`): number of digits after the decimal
       point to found the result, if not `None`

       sigfigs (int or `None`): number of significant digits to round
       the result, if not `None`

       string (bool): return output as a string (forces number of digits)
    """
    decimals = kwds.get("decimals", None)
    sigfigs = kwds.get("sigfigs", None)
    string = kwds.get("string", False)

    if len(values) == 1 and not isinstance(values[0], (numbers.Number, numpy.number)):
        values = values[0]

    sum_1 = 0.
    sum_y = 0.
    for y in values:
        if not isinstance(y, (numbers.Number, numpy.number)):
            raise ValueError, "mean() requires a list of numbers"

        sum_1 += 1.
        sum_y += y
    if sum_1 != 0.:
        output = sum_y / sum_1
        if decimals is not None:
            if string:
                return str_round(output, decimals)
            else:
                return round(output, decimals)
        elif sigfigs is not None:
            if string:
                return str_sigfigs(output, sigfigs)
            else:
                return round_sigfigs(output, sigfigs)
        else:
            if string:
                return str(output)
            else:
                return output
    else:
        raise ValueError, "Cannot take the mean without any values"

def wmean(values, weights, decimals=None, sigfigs=None, string=False):
    """Compute the weighted mean of N values with N weights (N > 0).

    Keyword arguments:
       decimals (int or `None`): number of digits after the decimal
       point to found the result, if not `None`

       sigfigs (int or `None`): number of significant digits to round
       the result, if not `None`

       string (bool): return output as a string (forces number of digits)
    """
    sum_1 = 0.
    sum_y = 0.
    for y, weight in itertools.izip(values, weights):
        if not isinstance(y, (numbers.Number, numpy.number)) or not isinstance(weight, (numbers.Number, numpy.number)):
            raise ValueError, "wmean() requires lists of numbers"

        sum_1 += weight
        sum_y += weight * y
    if sum_1 != 0.:
        outputval, outputerr = sum_y / sum_1, math.sqrt(1. / sum_1)
        if decimals is not None:
            if string:
                return str_round(outputval, decimals), str_round(outputerr, decimals)
            else:
                return round(outputval, decimals), round(outputerr, decimals)
        elif sigfigs is not None:
            if string:
                return str_errpair(outputval, outputerr, sigfigs)
            else:
                return round_errpair(outputval, outputerr, sigfigs)
        else:
            if string:
                return str(outputval), str(outputerr)
            else:
                return outputval, outputerr
    else:
        raise ValueError, "Cannot take the weighted mean without any values"

def linearfit(xvalues, yvalues, weights=None, decimals=None, sigfigs=None, string=False):
    """Compute a linear fit of N x-y pairs with weights (N > 0).

    Keyword arguments:
       weights (list of numbers or `None`): if `None`, weight all
       points equally.

       decimals (int or `None`): number of digits after the decimal
       point to found the result, if not `None`

       sigfigs (int or `None`): number of significant digits to round
       the result, if not `None`

       string (bool): return output as a string (forces number of digits)
    """
    if weights is None:
        weights = numpy.ones(min(len(xvalues), len(yvalues)), dtype=numpy.float)

    sum_1 = 0.
    sum_x = 0.
    sum_xx = 0.
    sum_y = 0.
    sum_xy = 0.
    for x, y, weight in itertools.izip(xvalues, yvalues, weights):
        if not isinstance(x, (numbers.Number, numpy.number)) or not isinstance(y, (numbers.Number, numpy.number)) or not isinstance(weight, (numbers.Number, numpy.number)):
            raise ValueError, "linearfit() requires lists of numbers"

        sum_1 += weight
        sum_x += weight * x
        sum_xx += weight * x**2
        sum_y += weight * y
        sum_xy += weight * x * y
    delta = (sum_1 * sum_xx) - (sum_x * sum_x)
    if delta != 0.:
        intercept = ((sum_xx * sum_y) - (sum_x * sum_xy)) / delta
        intercept_err = math.sqrt(sum_xx / delta)
        slope = ((sum_1 * sum_xy) - (sum_x * sum_y)) / delta
        slope_err = math.sqrt(sum_1 / delta)
        if decimals is not None:
            if string:
                intercept, intercept_err = str_round(intercept, decimals), str_round(intercept_err, decimals)
                slope, slope_err = str_round(slope, decimals), str_round(slope_err, decimals)
            else:
                intercept, intercept_err = round(intercept, decimals), round(intercept_err, decimals)
                slope, slope_err = round(slope, decimals), round(slope_err, decimals)
        elif sigfigs is not None:
            if string:
                intercept, intercept_err = str_errpair(intercept, intercept_err, sigfigs)
                slope, slope_err = str_errpair(slope, slope_err, sigfigs)
            else:
                intercept, intercept_err = round_errpair(intercept, intercept_err, sigfigs)
                slope, slope_err = round_errpair(slope, slope_err, sigfigs)
        elif string:
            intercept, intercept_err = str(intercept), str(intercept_err)
            slope, slope_err = str(slope), str(slope_err)
        return intercept, intercept_err, slope, slope_err
    else:
        raise ValueError, "Cannot take a linear fit without any values"

def rms(*values, **kwds):
    """Compute the root-mean-square of N values (N > 0).

    Keyword arguments:
       decimals (int or `None`): number of digits after the decimal
       point to found the result, if not `None`

       sigfigs (int or `None`): number of significant digits to round
       the result, if not `None`

       string (bool): return output as a string (forces number of digits)
    """
    decimals = kwds.get("decimals", None)
    sigfigs = kwds.get("sigfigs", None)
    string = kwds.get("string", False)

    if len(values) == 1 and not isinstance(values[0], (numbers.Number, numpy.number)):
        values = values[0]

    sum_1 = 0.
    sum_yy = 0.
    for y in values:
        if not isinstance(y, (numbers.Number, numpy.number)):
            raise ValueError, "rms() requires a list of numbers"

        sum_1 += 1.
        sum_yy += y**2
    if sum_1 != 0.:
        output = math.sqrt(sum_yy / sum_1)
        if decimals is not None:
            if string:
                return str_round(output, decimals)
            else:
                return round(output, decimals)
        elif sigfigs is not None:
            if string:
                return str_sigfigs(output, sigfigs)
            else:
                return round_sigfigs(output, sigfigs)
        else:
            if string:
                return str(output)
            else:
                return output
    else:
        raise ValueError, "Cannot take the RMS with fewer than one unique value"

def stdev(*values, **kwds):
    """Compute the standard deviation of N values (N > 0).

    Keyword arguments:
       unbiased (bool defaulting to True): return unbiased sample
       deviation, sqrt(sum(xi - mean)**2/(N - 1)), rather than the
       biased estimator, sqrt(sum(xi - mean)**2/ N )

       decimals (int or `None`): number of digits after the decimal
       point to found the result, if not `None`

       sigfigs (int or `None`): number of significant digits to round
       the result, if not `None`

       string (bool): return output as a string (forces number of digits)
    """
    unbiased = kwds.get("unbiased", True)
    decimals = kwds.get("decimals", None)
    sigfigs = kwds.get("sigfigs", None)
    string = kwds.get("string", False)

    if len(values) == 1 and not isinstance(values[0], (numbers.Number, numpy.number)):
        values = values[0]

    sum_1 = 0.
    sum_y = 0.
    sum_yy = 0.
    for y in values:
        if not isinstance(y, (numbers.Number, numpy.number)):
            raise ValueError, "stdev() requires a list of numbers"

        sum_1 += 1.
        sum_y += y
        sum_yy += y**2
    if sum_1 > 1. and (sum_yy / sum_1) > (sum_y / sum_1)**2:
        output = math.sqrt((sum_yy / sum_1) - (sum_y / sum_1)**2)

        if unbiased:
            output *= math.sqrt(sum_1 / (sum_1 - 1.))

        if decimals is not None:
            if string:
                return str_round(output, decimals)
            else:
                return round(output, decimals)
        elif sigfigs is not None:
            if string:
                return str_sigfigs(output, sigfigs)
            else:
                return round_sigfigs(output, sigfigs)
        else:
            if string:
                return str(output)
            else:
                return output
    else:
        raise ValueError, "Cannot take the stdev with fewer than one unique value"

def covariance(xvalues, yvalues, decimals=None, sigfigs=None, string=False):
    """Compute the covariance of N x-y pairs (N > 0).

    Keyword arguments:
       decimals (int or `None`): number of digits after the decimal
       point to found the result, if not `None`

       sigfigs (int or `None`): number of significant digits to round
       the result, if not `None`

       string (bool): return output as a string (forces number of digits)
    """
    xmean = mean(*xvalues)
    ymean = mean(*yvalues)
    sum_1 = 0.
    sum_xy = 0.
    for x, y in itertools.izip(xvalues, yvalues):
        sum_1 += 1.
        sum_xy += (x - xmean) * (y - ymean)
    output = sum_xy / sum_1
    if decimals is not None:
        if string:
            return str_round(output, decimals)
        else:
            return round(output, decimals)
    elif sigfigs is not None:
        if string:
            return str_sigfigs(output, sigfigs)
        else:
            return round_sigfigs(output, sigfigs)
    else:
        if string:
            return str(output)
        else:
            return output

def correlation(xvalues, yvalues, decimals=None, sigfigs=None, string=False):
    """Compute the correlation of N x-y pairs (N > 0).

    Keyword arguments:
       decimals (int or `None`): number of digits after the decimal
       point to found the result, if not `None`

       sigfigs (int or `None`): number of significant digits to round
       the result, if not `None`

       string (bool): return output as a string (forces number of digits)
    """
    xmean = mean(xvalues)
    ymean = mean(yvalues)
    sum_xx = 0.
    sum_yy = 0.
    sum_xy = 0.
    for x, y in itertools.izip(xvalues, yvalues):
        sum_xx += (x - xmean)**2
        sum_yy += (y - ymean)**2
        sum_xy += (x - xmean) * (y - ymean)
    if sum_xx + sum_yy != 0.:
        output = sum_xy / math.sqrt(sum_xx + sum_yy)
        if decimals is not None:
            if string:
                return str_round(output, decimals)
            else:
                return round(output, decimals)
        elif sigfigs is not None:
            if string:
                return str_sigfigs(output, sigfigs)
            else:
                return round_sigfigs(output, sigfigs)
        else:
            if string:
                return str(output)
            else:
                return output
    else:
        raise ValueError, "Cannot take the correlation without any values"

def ubiquitous(array):
    """Return the most ubiquitous (most frequent) member of a list."""

    if isinstance(array, numpy.ndarray):
        keys = numpy.unique(array)
        maximal = None
        for k in keys:
            this = len(array[array == k])
            if maximal is None or this > maximal:
                maximal_key = k
                maximal = this
        if maximal is not None:
            return maximal_key
        else:
            return None

    else:
        keys = set(array)
        maximal = None
        for k in keys:
            this = len(array.count(k))
            if maximal is None or this > maximal:
                maximal_key = k
                maximal = this
        if maximal is not None:
            return maximal_key
        else:
            return None

def erf(x):
    """Return the error function of x.

    (For complex erf, get SciPy and load scipy.special)
    """

    # http://stackoverflow.com/questions/457408/is-there-an-easily-available-implementation-of-erf-for-python
    sign = 1
    if x < 0: 
        sign = -1
    x = abs(x)

    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911

    # http://www.amazon.com/dp/0486612724/?tag=stackoverfl08-20 formula 7.1.26
    t = 1.0/(1.0 + p*x)
    y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*math.exp(-x*x)
    return sign*y # erf(-x) = -erf(x)

def erfc(x):
    """Return 1 minus the error function of x.

    (For complex erfc, get SciPy and load scipy.special)
    """
    return 1. - erf(x)

def gaussian_likelihood(f, x, y, ey):
    """Gaussian likelihood function usable in Curve.objective and Curve.fit.

    Expression:

       (f - y)**2 / ey**2  or  0 if ey == 0

       where f is the value of the curve at x, y is the data, and ey
       is the uncertainty in the data (one Gaussian sigma).
    """

    return ((f - y)**2/ey**2 if ey != 0. else 0.)

def poisson_likelihood(f, x, y):
    """Poisson likelihood function usable in Curve.objective and Curve.fit.

    Expression:

       -2 * (y * log(f) - f - log(y!))

       where f is the value of the curve at x and y is the data
       (usually an integer, like a histogram bin value).

    Considerations:

       Note the factor of 2!  Not all texts include this factor.  With
       the factor of 2, this Poisson likelihood can be used
       interchangeably with a Gaussian likelihood (i.e. chi^2):
       uncertainty in a best fit value is the distance you need to
       walk to raise this objective function by 1.0, just like the
       Gaussian likelihood (not 0.5!).
    """

    # try:
    #     return -2.*(y*math.log(f) - f - math.log(math.factorial(y)))
    # except ValueError:
    #     return -2.*(y*math.log(1e-10) - 1e-10 - math.log(math.factorial(y)))

    ### much better:
    try:
        return -2.*(y*math.log(f) - f - sum(map(math.log, xrange(1, y+1))))
    except ValueError:
        # note: if f == 0., then any non-zero y is impossible
        # is it right to give it a small value?  something to think about...
        return -2.*(y*math.log(1e-10) - 1e-10 - sum(map(math.log, xrange(1, y+1))))


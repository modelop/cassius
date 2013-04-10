# Standard Python packages
import math
import numbers
import time

# Special dependencies
import numpy

# Cassius interdependencies
import mathtools

def unicode_number(x):
  """Convert a number to unicode, with appropriate substitutions."""

  output = u"%g" % x

  if output[0] == u"-":
    output = u"\u2012" + output[1:]

  index = output.find(u"e")
  if index != -1:
    uniout = unicode(output[:index]) + u"\u00d710"
    saw_nonzero = False
    for n in output[index+1:]:
      if n == u"+": pass # uniout += u"\u207a"
      elif n == u"-": uniout += u"\u207b"
      elif n == u"0":
        if saw_nonzero: uniout += u"\u2070"
      elif n == u"1":
        saw_nonzero = True
        uniout += u"\u00b9"
      elif n == u"2":
        saw_nonzero = True
        uniout += u"\u00b2"
      elif n == u"3":
        saw_nonzero = True
        uniout += u"\u00b3"
      elif u"4" <= n <= u"9":
        saw_nonzero = True
        if saw_nonzero: uniout += eval("u\"\\u%x\"" % (0x2070 + ord(n) - ord(u"0")))
      else: uniout += n

    if uniout[:2] == u"1\u00d7": uniout = uniout[2:]
    return uniout

  return output

def regular(step, start=0.):
    """Return a function that can be used to draw regular grid lines
    or tick marks.

    Arguments:
       step (number): size of the spacing

       start (number): starting value, indicating the offset

    Returns:
       The function, `f(low, high)` returned by `regular` maps
       endpoints `low` and `high` to a numpy array of values
       satisfying `step` and `start` between `low` and `high`.

    Example::

       >>> reg = regular(1., start=0.5)
       >>> reg
       <function regular(1, start=0.5) at 0x1e889b0>
       >>> reg(0, 10)
       array([ 0.5,  1.5,  2.5,  3.5,  4.5,  5.5,  6.5,  7.5,  8.5,  9.5])
    """

    def output(low, high):
        newstart = math.ceil((low - start)/step) * step + start
        return numpy.arange(newstart, high, step, dtype=numpy.float)
    output.func_name = "regular(%g, start=%g)" % (step, start)
    return output

def _compute_majorticks(low, high, N, format):
    eps = mathtools.epsilon * (high - low)

    if N >= 0:
        output = {}
        x = low
        for i in xrange(N):
            if format == unicode_number and abs(x) < eps: label = u"0"
            else: label = format(x)
            output[x] = label
            x += (high - low)/(N-1.)
        return output

    N = -N

    counter = 0
    granularity = 10**math.ceil(math.log10(max(abs(low), abs(high))))
    lowN = math.ceil(1.*low / granularity)
    highN = math.floor(1.*high / granularity)

    while (lowN > highN):
        countermod3 = counter % 3
        if countermod3 == 0: granularity *= 0.5
        elif countermod3 == 1: granularity *= 0.4
        else: granularity *= 0.5
        counter += 1
        lowN = math.ceil(1.*low / granularity)
        highN = math.floor(1.*high / granularity)

    last_granularity = granularity
    last_trial = None

    while True:
        trial = {}
        for n in range(int(lowN), int(highN)+1):
            x = n * granularity
            if format == unicode_number and abs(x) < eps: label = u"0"
            else: label = format(x)
            trial[x] = label

        if int(highN)+1 - int(lowN) >= N:
            if last_trial == None:
                v1, v2 = low, high
                return {v1: format(v1), v2: format(v2)}
            else:
                low_in_ticks, high_in_ticks = False, False
                for t in last_trial.keys():
                    if 1.*abs(t - low)/last_granularity < mathtools.epsilon: low_in_ticks = True
                    if 1.*abs(t - high)/last_granularity < mathtools.epsilon: high_in_ticks = True

                lowN = 1.*low / last_granularity
                highN = 1.*high / last_granularity
                if abs(lowN - round(lowN)) < mathtools.epsilon and not low_in_ticks:
                    last_trial[low] = format(low)
                if abs(highN - round(highN)) < mathtools.epsilon and not high_in_ticks:
                    last_trial[high] = format(high)
                return last_trial

        last_granularity = granularity
        last_trial = trial

        countermod3 = counter % 3
        if countermod3 == 0: granularity *= 0.5
        elif countermod3 == 1: granularity *= 0.4
        else: granularity *= 0.5
        counter += 1
        lowN = math.ceil(1.*low / granularity)
        highN = math.floor(1.*high / granularity)

def _compute_minorticks(low, high, major_ticks):
    if len(major_ticks) < 2: major_ticks = {low: None, high: None}
    major_ticks = major_ticks.keys()
    major_ticks.sort()

    granularities = []
    for i in range(len(major_ticks)-1):
        granularities.append(major_ticks[i+1] - major_ticks[i])
    spacing = 10**(math.ceil(math.log10(min(granularities)) - 1))

    output = {}
    x = major_ticks[0] - math.ceil(1.*(major_ticks[0] - low) / spacing) * spacing

    while x <= high:
        if x >= low:
            already_in_ticks = False
            for t in major_ticks:
                if abs(x-t) < mathtools.epsilon * (high - low): already_in_ticks = True
            if not already_in_ticks: output[x] = None
        x += spacing
    return output

def _compute_logmajorticks(low, high, base, N, format):
    if low >= high: raise ValueError, "low must be less than high"
    if N == 1: raise ValueError, "N can be 0 or >1 to specify the exact number of ticks or negative to specify a maximum"

    eps = mathtools.epsilon * (high - low)

    if N >= 0:
      output = {}
      x = low
      for i in xrange(N):
        if format == unicode_number and abs(x) < eps: label = u"0"
        else: label = format(x)
        output[x] = label
        x += (high - low)/(N-1.)
      return output

    N = -N

    lowN = math.floor(math.log(low, base))
    highN = math.ceil(math.log(high, base))
    output = {}
    for n in range(int(lowN), int(highN)+1):
      x = base**n
      label = format(x)
      if low <= x <= high: output[x] = label

    for i in range(1, len(output)):
      keys = output.keys()
      keys.sort()
      keys = keys[::i]
      values = map(lambda k: output[k], keys)
      if len(values) <= N:
        for k in output.keys():
          if k not in keys:
            output[k] = ""
        break

    if len(output) <= 2:
      output2 = _compute_majorticks(low, high, N=-int(math.ceil(N/2.)), format=format)
      lowest = min(output2)

      for k in output:
        if k < lowest: output2[k] = output[k]
      output = output2

    return output

def _compute_logminorticks(low, high, base):
    if low >= high: raise ValueError, "low must be less than high"

    lowN = math.floor(math.log(low, base))
    highN = math.ceil(math.log(high, base))
    output = {}
    num_ticks = 0
    for n in range(int(lowN), int(highN)+1):
      x = base**n
      if low <= x <= high: num_ticks += 1
      for m in range(2, int(math.ceil(base))):
        minix = m * x
        if low <= minix <= high: output[minix] = None

    if num_ticks <= 2: return {}
    else: return output

def tickmarks(major=-10, minor=True, logbase=0, format=unicode_number):
    """Return a function that can be used to set standard tick marks.

    Arguments:
       major (number): exact number (if positive) or a maximum number of
       "natural" values (multiples of 2 or 5) for the major (labeled) ticks

       minor (bool): if True, also include minor (unlabeled) ticks
       between the major ones

       logbase (int): if 0, produce regular ticks; if positive, treat
       as a base for logarithmic ticks

       format (function or string): used to set labels of major ticks;
       either a function mapping numbers to strings or a standard
       format specifier (e.g. "%g", "%.2f", etc.)

    Considerations:
       To split a region into N equal-sized segments, ask for N+1
       ticks.

    Examples::

       >>> ticks = tickmarks(minor=False, format="%g")
       >>> ticks
       <function tickmarks(major=-10, minor=False, logbase=0, format=%g) at 0x1b579b0>
       # a function that can later be used to set tick-marks
       >>> ticks(0., 10.)
       {0.0: '0', 2.0: '2', 4.0: '4', 6.0: '6', 8.0: '8', 10.0: '10'}

       >>> ticks = tickmarks(minor=False, logbase=10)
       >>> ticks(10**7, 10**10)
       {10000000: u'10\\u2077', 100000000: u'10\\u2078', 1000000000: u'10\\u2079', 10000000000: u'10\\xb9\\u2070'}
       # the strings are unicode for 10^{7}, 10^{8}, 10^{9}, 10^{10}

       >>> ticks = tickmarks(3, format="%g")
       >>> ticks(0., 1.)
       {0: '0', 0.5: '0.5', 0.2: None, 0.4: None, 1.0: '1', 0.3: None, 0.6: None, 0.1: None, 0.9: None, 0.7: None, 0.8: None}
       # three major (labeled) tick-marks with minor tick-marks (labels=None) filling in the gaps
    """

    if not callable(format):
        tmp = format
        format = lambda x: tmp % x
        format.func_name = tmp

    def linear_tickmarks(low, high):
        if low >= high:
            raise ValueError, "To compute tick-marks, 'low' must be lower than 'high'."

        major_ticks = _compute_majorticks(low, high, major, format)
        if minor:
            minor_ticks = _compute_minorticks(low, high, major_ticks)
        else:
            minor_ticks = {}
        minor_ticks.update(major_ticks)
        return minor_ticks

    def logarithmic_tickmarks(low, high):
        if low >= high:
            raise ValueError, "To compute tick-marks, 'low' must be lower than 'high'."

        major_ticks = _compute_logmajorticks(low, high, logbase, major, format)
        if minor:
            minor_ticks = _compute_logminorticks(low, high, logbase)
        else:
            minor_ticks = {}
        minor_ticks.update(major_ticks)
        return minor_ticks

    if logbase == 0: output = linear_tickmarks
    else: output = logarithmic_tickmarks

    output.func_name = "tickmarks(major=%d, minor=%s, logbase=%d, format=%s)" % (major, repr(minor), logbase, format.func_name)
    return output

def calcrange(data, log=False):
    """Return the range (min, max) of a dataset, excluding any NANs."""
    xmin, xmax = None, None
    for x in data:
        if not log or x > 0.:
            if xmin is None or x < xmin: xmin = x
            if xmax is None or x > xmax: xmax = x

    if xmin is None and xmax is None:
        if log:
            return 0.1, 1.
        else:
            return 0., 1.
    else:
        return xmin, xmax

def calcrange_quartile(data, log=False):
    """Return the range (min, max) of a dataset, based on quartiles (stable against large numbers)."""
    if not isinstance(data, numpy.ndarray):
        data = numpy.array(data)
    if log:
        data = data[data > 0.]

    if len(data) == 0:
        if log: return 0.1, 1.
        else: return 0., 1.

    data = numpy.sort(data)
    q1 = data[int(math.floor(0.25*len(data)))]
    q3 = data[int(math.floor(0.75*len(data)))]
    if log:
        return q1 / (q3 - q1), q3 * (q3 - q1)
    else:
        return q1 - (q3 - q1), q3 + (q3 - q1)

def binning(data, low, high):
    """Return a number of bins for this dataset using the Freedman-Diaconis rule."""
    if len(data) == 0: return 1

    mask1 = (data >= low)
    mask2 = (data < high)
    mask3 = numpy.logical_and(mask1, mask2)
    data = data[mask3]

    if len(data) == 0: return 10

    data.sort()
    q1 = data[int(math.floor(0.25*len(data)))]
    q3 = data[int(math.floor(0.75*len(data)))]
    binwidth = 2. * (q3 - q1) / len(data)**(1./3.)
    if binwidth > 0.:
        return max(10, int(math.ceil((high - low)/binwidth)))
    else:
        return 10
    
def binning_sturges(data, low, high):
    raise NotImplementedError # FIXME

def timesec(year=None, month=None, day=None, hour=None, min=None, sec=None):
    """Quickly obtain a number of seconds from the current time or a given time.

    Arguments:
       year (int): give a specific year; overrides current year

       month (int): give a specific month; overrides current month

       day (int): give a specific day of the month; overrides current day

       hour (int): give a specific hour (24-hour clock); overrides current hour

       min (int): give a specific minute; overrides current minute

       sec (int): give a specific second; overrides current second

    Returns:
       Number of seconds since epoch (Jan 1, 1970) as a float with
       fractional seconds.  For the nearest number of seconds, round
       the output.
    """

    seconds, subsecs = divmod(time.time(), 1)
    now = time.gmtime(int(seconds))
    if year is None: year = now.tm_year
    if month is None: month = now.tm_mon
    if day is None: day = now.tm_mday
    if hour is None: hour = now.tm_hour
    if min is None: min = now.tm_min
    if sec is None: sec = now.tm_sec
    return time.mktime(time.struct_time((year, month, day, hour, min, sec, -1, -1, -1))) + subsecs

def fromtimestring(timestrings, format, subseconds=False, t0=0.):
    """Convert a time string or many time strings into a number(s) of seconds.

    Arguments:
       timestring (string or list of strings): time string(s) to be
       converted

       format (string): time formatting string (see `time
       documentation
       <http://docs.python.org/library/time.html#time.strftime>`_)

       subseconds (bool): if True, interpret ".xxx" at the end of
       the string as fractions of a second

       t0 (number or time-string): the time from which to start
       counting; zero is equivalent to Jan 1, 1970

    Behavior:
       If only one `timestring` is passed, the return value is a
       single number; if a list of strings is passed, the return value
       is a list of numbers.

       Subseconds are _always_ at the end of the string, regardless of
       where the seconds appear in the format (if at all).
    """

    if isinstance(t0, (numbers.Number, numpy.number)) or format is None:
        t0 = float(t0)
    else:
        if subseconds:
            pytimestring, subsecs = t0.split(".")
            subsecs = float("0." + subsecs)
        else:
            pytimestring, subsecs = t0, 0.
        tmp = time.strptime(pytimestring, format)
        tmp = [tmp.tm_year, tmp.tm_mon, tmp.tm_mday, tmp.tm_hour, tmp.tm_min, tmp.tm_sec, tmp.tm_wday, tmp.tm_yday, tmp.tm_isdst]
        if format.find("%y") == -1 and format.find("%Y") == -1:
            tmp[0] = 1970
        tzoffset = 0
        if format.find("%Z") == -1:
            # if time.daylight:
            #     tzoffset = time.altzone
            # else:
                tzoffset = time.timezone
        t0 = time.mktime(tuple(tmp)) - tzoffset + subsecs

    single_value = False
    if isinstance(timestrings, basestring):
        single_value = True
        timestrings = [timestrings]

    output = numpy.empty(len(timestrings), dtype=numpy.float)
    for i, timestring in enumerate(timestrings):
        if format is None:
            output[i] = float(timestring)
        else:
            if subseconds:
                pytimestring, subsecs = timestring.split(".")
                subsecs = float("0." + subsecs)
            else:
                pytimestring, subsecs = timestring, 0.
            tmp = time.strptime(pytimestring, format)
            tmp = [tmp.tm_year, tmp.tm_mon, tmp.tm_mday, tmp.tm_hour, tmp.tm_min, tmp.tm_sec, tmp.tm_wday, tmp.tm_yday, tmp.tm_isdst]
            if format.find("%y") == -1 and format.find("%Y") == -1:
                tmp[0] = 1970
            tzoffset = 0
            if format.find("%Z") == -1:
                # if time.daylight:
                #     tzoffset = time.altzone
                # else:
                    tzoffset = time.timezone
            output[i] = time.mktime(tuple(tmp)) - tzoffset + subsecs - t0

    if single_value: return output[0]
    else: return output

def totimestring(timenumbers, format, subseconds=False, t0=0.):
    """Convert a number of seconds or a list of numbers into time string(s).

    Arguments:
       timenumbers (number or list of numbers): time(s) to be
       converted

       format (string): time formatting string (see `time
       documentation
       <http://docs.python.org/library/time.html#time.strftime>`_)

       subseconds (bool): if True, append ".xxx" at the end of
       the string as fractions of a second

       t0 (number or time-string): the time from which to start
       counting; zero is equivalent to Jan 1, 1970

    Behavior:
       If only one `timenumbers` is passed, the return value is a
       single string; if a list of strings is passed, the return value
       is a list of strings.

       Subseconds are _always_ at the end of the string, regardless of
       where the seconds appear in the format (if at all).
    """

    if isinstance(t0, (numbers.Number, numpy.number)):
        t0 = float(t0)
    else:
        if subseconds:
            pytimestring, subsecs = t0.split(".")
            subsecs = float("0." + subsecs)
        else:
            pytimestring, subsecs = t0, 0.
        tmp = time.strptime(pytimestring, format)
        tmp = [tmp.tm_year, tmp.tm_mon, tmp.tm_mday, tmp.tm_hour, tmp.tm_min, tmp.tm_sec, tmp.tm_wday, tmp.tm_yday, tmp.tm_isdst]
        if format.find("%y") == -1 and format.find("%Y") == -1:
            tmp[0] = 1970
        tzoffset = 0
        if format.find("%Z") == -1:
            # if time.daylight:
            #     tzoffset = time.altzone
            # else:
                tzoffset = time.timezone
        t0 = time.mktime(tuple(tmp)) - tzoffset + subsecs

    single_value = False
    if isinstance(timenumbers, (numbers.Number, numpy.number)):
        single_value = True
        timenumbers = [timenumbers]
        
    output = []
    for timenumber in timenumbers:
        if subseconds:
            subsecs, secs = math.modf(timenumber + t0)
            ss = str(abs(subsecs))[2:]
            if ss == "0":
                output.append(time.strftime(format, time.gmtime(int(secs))))
            else:
                output.append("%s.%s" % (time.strftime(format, time.gmtime(int(secs))), ss))
        else:
            secs = round(timenumber + t0)
            output.append(time.strftime(format, time.gmtime(int(secs))))

    if single_value: return output[0]
    else: return output

def timeticks(major, minor, format="%Y-%m-%d %H:%M:%S", subseconds=False, t0=0., start=None):
    """Set x tick-marks to temporally meaningful values.

    Arguments:
       major (number): number of seconds interval (may use combinations
       of SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, or YEAR constants)
       for major ticks (ticks with labels)

       minor (number): same for minor ticks (shorter ticks without labels)

       format (string): time format (see `time documentation
       <http://docs.python.org/library/time.html#time.strftime>`_)

       subseconds (bool): if True, interpret ".xxx" at the end of
       the string as fractions of a second

       t0 (number or time-string): the time from which to start
       counting; zero is equivalent to Jan 1, 1970

       start (number, string, or `None`): a time to set the offset
       of the tick-marks (use `t0` if `None`)

    Behavior:
       A "month" is taken to be exactly 31 days and a "year" is
       taken to be exactly 365 days.  Week markers will only line
       up with month markers at `start`.
    """

    if start is None: start = t0

    if isinstance(start, basestring): start = fromtimestring(start, format, subseconds, t0)

    def timeticks(low, high):
        newstart = math.ceil((low - start)/major) * major + start
        return dict(map(lambda x: (x, totimestring(x, format, subseconds, t0)), numpy.arange(newstart, high, major, dtype=numpy.float)))

    def timeminiticks(low, high):
        newstart = math.ceil((low - start)/minor) * minor + start
        return dict(map(lambda x: (x, None), numpy.arange(newstart, high, minor, dtype=numpy.float)))

    return timeticks, timeminiticks

SECOND = 1.
MINUTE = 60.
HOUR = 60.*60.
DAY = 60.*60.*24.
WEEK = 60.*60.*24.*7.
MONTH = 60.*60.*24.*31.
YEAR = 60.*60.*24.*356.

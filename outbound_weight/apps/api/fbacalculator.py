from decimal import Decimal, ROUND_UP, InvalidOperation
from numpy import median

from .constants import NOVEMBER_DECEMBER, JANUARY_OCTOBER, \
    OCTOBER_DECEMBER, JANUARY_SEPTEMBER
from . import constants

""" Calculate FBA fees """

TWO_PLACES = Decimal("0.01")


def _30_day(standard_oversize, cubic_foot):
    return constants.THIRTY_DAY[standard_oversize] * normalize(cubic_foot)


def _standard_or_oversize(length, width, height, weight):
    """ Determine if object is standard size or oversized """
    if any([(weight > 20),
            (max(length, width, height) > 18),
            (min(length, width, height) > 8),
            (median([length, width, height]) > 14)]):
        return "Oversize"
    return "Standard"


def normalize(data):
    if type(data) != Decimal:
        return Decimal(str(data))
    return data


def _dimensional_weight(length, width, height):
    dw = (height * length * width) / constants.DIMENSIONAL_WEIGHT_DIVISOR
    return Decimal(dw).quantize(TWO_PLACES)


def _girth_and_length(length, width, height):
    gl = max(length, width, height) + \
        (median([length, width, height]) * 2) + \
        (min(length, width, height) * 2)

    return Decimal(gl).quantize(Decimal("0.1"))


def _cubic_foot(length, width, height):
    return (length * width * height) / constants.CUBIC_FOOT_DIVISOR


def _weight_handling(size_tier, outbound, price=Decimal('0'), is_media=False):
    if price >= 300:
        return Decimal('0')
    outbound = normalize(outbound).quantize(Decimal("0"), rounding=ROUND_UP)

    if size_tier == "SML_STND":
        return Decimal('0.5')

    if size_tier == "LRG_STND":

        if is_media:
            if outbound <= 1:
                return Decimal('0.85')
            if outbound <= 2:
                return Decimal('1.24')
            return Decimal('1.24') + (outbound - 2) * Decimal('0.41')

        if outbound <= 1:
            return Decimal('0.96')
        if outbound <= 2:
            return Decimal('1.95')
        return Decimal('1.95') + (outbound - 2) * Decimal('0.39')

    if size_tier == "SPL_OVER":
        if outbound <= 90:
            return Decimal("124.58")
        return Decimal('124.58') + (outbound - 90) * Decimal('0.92')

    if size_tier == "LRG_OVER":
        if outbound <= 90:
            return Decimal("63.98")
        return Decimal('63.98') + (outbound - 90) * Decimal('0.8')

    if size_tier == "MED_OVER":
        if outbound <= 2:
            return Decimal("2.73")
        return Decimal('2.73') + (outbound - 2) * Decimal('0.39')

    if outbound <= 2:
        return Decimal('2.06')
    return Decimal('2.06') + (outbound - 2) * Decimal('0.39')


def calculate_fees(length, width, height, weight, sales_price=Decimal("0"),
                   is_apparel=False, is_media=False, is_pro=True):
    """ Calculate the FBA fees for the given variables """
    # Make sure the values are decimals
    length, width = normalize(length), normalize(width)
    height, weight = normalize(height), normalize(weight)

    dimensional_weight = _dimensional_weight(length, width, height)
    girth_length = _girth_and_length(length, width, height)

    standard_oversize = _standard_or_oversize(length, width, height, weight)

    cubic_foot = _cubic_foot(length, width, height)

    if standard_oversize == "Standard":
        if is_media:
            fee_weight = constants.FEE_WEIGHT_MEDIA
        else:
            fee_weight = constants.FEE_WEIGHT

        if all(
            [
                (fee_weight >= weight),
                (max(length, width, height) <= Decimal('15')),
                (min(length, width, height) <= Decimal('0.75')),
                (median([length, width, height]) <= Decimal('12'))
            ]
        ):
            size_tier = "SML_STND"
        else:
            size_tier = "LRG_STND"
    else:
        if any(
            [
                (girth_length > 165),
                (weight > 150),
                (max(length, width, height) > 108),
             ]
        ):
            size_tier = "SPL_OVER"
        elif girth_length > 130:
            size_tier = "LRG_OVER"
        elif any(
            [
                (weight > 70),
                (max(length, width, height) > 60),
                (median([length, width, height]) > 30),
            ]
        ):
            size_tier = "MED_OVER"
        else:
            size_tier = "SML_OVER"

    if is_media:
        outbound = weight + Decimal("0.125")
    else:
        if standard_oversize == "Standard":
            if weight <= 1:
                outbound = weight + Decimal('0.25')
            else:
                outbound = max(weight, dimensional_weight) + Decimal('0.25')
        else:
            if size_tier == "SPL_OVER":
                outbound = weight + 1
            else:
                outbound = max(weight, dimensional_weight) + 1

    if is_media or standard_oversize == "Oversize":
        order_handling = 0
    else:
        order_handling = 1

    if sales_price >= 300:
        pick_pack = 0
    else:
        pick_pack = constants.PICK_PACK.get(standard_oversize, constants.PICK_PACK.get(size_tier))

    weight_handling = _weight_handling(
        size_tier, outbound, sales_price, is_media).quantize(TWO_PLACES)

    thirty_day = _30_day(standard_oversize, cubic_foot)

    costs = normalize(pick_pack) + \
        normalize(weight_handling) + \
        normalize(thirty_day) + \
        normalize(order_handling)

    # Add the referral fees if we know how much we plan to sell the product for
    if sales_price:
        referral_fee = sales_price * constants.CLOSING_FEES['referral']
        costs += referral_fee.quantize(TWO_PLACES)

    if is_media:
        costs += constants.CLOSING_FEES['media']

    if is_apparel:
        costs += constants.CLOSING_FEES['apparel']

    if not is_pro:
        costs += constants.CLOSING_FEES['non-pro']

    return costs.quantize(TWO_PLACES)


def standart_oversize(length, width, height, weight):
    """
     Standard or oversize item
    """
    if any([(weight > 20),
            (max(length, width, height) > 18),
            (min(length, width, height) > 8),
            (median([length, width, height]) > 14)]):
        return 'Oversize'
    return 'Standard'


def length_girth(lenght, width, height):
    lg = max(lenght, width, height) \
         + (median([lenght, width, height]) * 2) \
         + (min(lenght, width, height) * 2)
    return Decimal(lg).quantize(Decimal('0.1'))


def normalize_dimensions(length, width, height, weight):
    dimensions_dict = dict(
        length=Decimal(str(length)),
        width=Decimal(str(width)),
        height=Decimal(str(height)))
    try:
        dimensions_dict['weight'] = Decimal(str(weight))
    except InvalidOperation as e:
        calculated_weight = (
            dimensions_dict['height'] *
            dimensions_dict['length'] *
            dimensions_dict['width']) / Decimal('166.0')
        dimensions_dict['weight'] = Decimal(calculated_weight).quantize(Decimal('0.1'))
    return dimensions_dict


def determine_size_tier(length, width, height, weight, is_media=False):
    length_and_girth = length_girth(length, width, height)
    if standart_oversize(length, width, height, weight) == 'Standard' and not is_media:
        fee_weight = 12.0 / 16.0
        if all([
            (fee_weight >= weight),
            (max(length, width, height) <= Decimal('15')),
            (min(length, width, height) <= Decimal('0.75')),
            (median([length, width, height]) <= Decimal('12'))
        ]):
            size_tier = 'Sm-Std-Non-Media'
        else:
            size_tier = 'Lg-Std-Non-Media'
    elif standart_oversize(length, width, height, weight) == 'Standard' and is_media:
        fee_weight = 14.0 / 16.0
        if all([
            (fee_weight >= weight),
            (max(length, width, height) <= Decimal('15')),
            (min(length, width, height) <= Decimal('0.75')),
            (median([length, width, height]) <= Decimal('12'))
        ]):
            size_tier = 'Sm-Std-Media'
        else:
            size_tier = 'Lg-Std-Media'
    else:
        if any([
            (length_and_girth > 165),
            (weight > 150),
            (max(length, width, height) > 100),
        ]):
            size_tier = 'Sp-Oversize'
        elif length_and_girth > 130:
            size_tier = 'Lg-Oversize'
        elif any([
            (weight > 70),
            (max(length, width, height) > 60),
            (median([length, width, height]) > 30),
        ]):
            size_tier = 'Md-Oversize'
        else:
            size_tier = 'Sm-Oversize'
    return size_tier


def get_rate_period(date):
    period = ''
    if date.month in NOVEMBER_DECEMBER and date.year == 2016:
        period = '11/1/{0} - 12/31/{0}'.format(date.strftime('%y'))
    elif date.month in JANUARY_OCTOBER and date.year == 2016:
        period = '1/1/{0} - 10/31/{0}'.format(date.strftime('%y'))
    elif date.month in OCTOBER_DECEMBER:
        period = '10/1/{0} - 12/31/{0}'.format(date.strftime('%y'))
    elif date.month in JANUARY_SEPTEMBER:
        period = '1/1/{0} - 9/30/{0}'.format(date.strftime('%y'))
    return period

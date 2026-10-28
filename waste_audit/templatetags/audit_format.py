from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def amount(value):
    if value is None:
        return ""
    text = format(Decimal(str(value)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


@register.filter
def rupiah(value):
    if value is None:
        return "Belum diisi"
    number = Decimal(str(value))
    digits = 0 if number == number.to_integral_value() else 2
    return "Rp" + format(number, f",.{digits}f").translate(str.maketrans({",": ".", ".": ","}))

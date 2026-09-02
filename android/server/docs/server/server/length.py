def convert_length(text):
    try:
        t = text.lower().replace(",", ".")

        if " у " not in t:
            return None

        left, unit2 = t.split(" у ")
        value, unit1 = left.split()

        value = float(value)

        if unit1 == "км" and unit2 == "м":
            return str(value * 1000)

        if unit1 == "м" and unit2 == "км":
            return str(value / 1000)

        if unit1 == "м" and unit2 == "см":
            return str(value * 100)

        if unit1 == "см" and unit2 == "м":
            return str(value / 100)

        if unit1 == "см" and unit2 == "мм":
            return str(value * 10)

        if unit1 == "мм" and unit2 == "см":
            return str(value / 10)

        if unit1 == "м" and unit2 == "мм":
            return str(value * 1000)

        if unit1 == "мм" and unit2 == "м":
            return str(value / 1000)

        return None

    except:
        return None

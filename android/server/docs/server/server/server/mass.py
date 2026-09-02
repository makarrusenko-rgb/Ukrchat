def convert_mass(text):
    try:
        t = text.lower().replace(",", ".")

        if " у " not in t:
            return None

        left, unit2 = t.split(" у ")
        value, unit1 = left.split()

        value = float(value)

        if unit1 == "кг" and unit2 == "г":
            return str(value * 1000)

        if unit1 == "г" and unit2 == "кг":
            return str(value / 1000)

        if unit1 == "г" and unit2 == "мг":
            return str(value * 1000)

        if unit1 == "мг" and unit2 == "г":
            return str(value / 1000)

        if unit1 == "кг" and unit2 == "мг":
            return str(value * 1000000)

        if unit1 == "мг" and unit2 == "кг":
            return str(value / 1000000)

        return None

    except:
        return None

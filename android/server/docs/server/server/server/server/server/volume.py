def convert_volume(text):
    try:
        t = text.lower().replace(",", ".")

        if " у " not in t:
            return None

        left, unit2 = t.split(" у ")
        value, unit1 = left.split()

        value = float(value)

        if unit1 == "л" and unit2 == "мл":
            return str(value * 1000)

        if unit1 == "мл" and unit2 == "л":
            return str(value / 1000)

        return None

    except:
        return None

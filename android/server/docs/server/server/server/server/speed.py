def convert_speed(text):
    try:
        t = text.lower().replace(",", ".")

        if " у " not in t:
            return None

        left, unit2 = t.split(" у ")
        value, unit1 = left.split()

        value = float(value)

        # км/год ↔ м/с
        if unit1 == "км/год" and unit2 == "м/с":
            return str(value / 3.6)

        if unit1 == "м/с" and unit2 == "км/год":
            return str(value * 3.6)

        return None

    except:
        return None

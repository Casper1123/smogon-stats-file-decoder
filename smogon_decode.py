# Classes
class RegistryError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Error404(Exception):
    def __init__(self, message):
        super().__init__(message)


class UnfoundMon(Exception):
    def __init__(self, message):
        super().__init__(message)


# Functions
def get_moveset_file(year: int, month: int, generation: int, gamemode: str, mmr: int) -> str:
    """
    :param year: The year (I.E. '2021')
    :param month: The month (I.E. '5', '05', '11')
    :param generation: The generation (I.E. '5')
    :param gamemode: The gamemode (I.E. 'ou')
    :param mmr: The average mmr the data should be from. Usually available at 0, 1500, 1630, 1760 with some exceptions.
    :return: a LOOOOOONG string containing all the data from the file. This is raw.
    """
    from datetime import datetime
    import requests

    now = datetime.now()
    if (year == now.year and month >= now.month) or year > now.year:
        raise RegistryError("Smogon only has files on past months and years.")
    if len(str(month)) < 2:
        month = f"0{month}"
    data = requests.get(f"https://www.smogon.com/stats/{year}-{month}/moveset/gen{generation}{gamemode.lower()}-{mmr}.txt").text
    if f"{data}" == "<html>":
        raise Error404("Did not find a file with given arguments.")
    return data


def get_mon_data_from_moveset_file(moveset_file: list or str, pokemon_name: str) -> dict:
    dataset = decode_smogon_moveset_data(moveset_file)
    for mon in dataset:
        if mon["name"].lower() == pokemon_name.lower():
            return mon
    raise UnfoundMon(f"Did not find '{pokemon_name}' in the submitted Smogon Moveset file. Be sure that it is exactly the same as the files say. It is just an a == b check that this runs.")


def decode_smogon_moveset_data(moveset_file: list[str] or str) -> list[dict]:
    def float_int(number: float) -> bool:
        return abs(number - int(number)) < .01

    def raw_line_splitter(raw_line) -> list:
        raw_split_line_f = raw_line.replace("%", "").split("| ")[1].split(" ")
        split_line_f = []
        for entry_f in raw_split_line_f:
            if entry_f not in ["", "|"]:
                split_line_f.append(entry_f)
        return split_line_f

    # Defines some important in-function constants
    datadict = {
        "name": "",
        "general": {
            "raw_count": None,
            "avg_weight": None,
            "viability_ceiling": None},
        "abilities": [],
        "items": [],
        "spreads": [],
        "moves": [],
        "teammates": [],
        "checks_and_counters": []
    }
    dividers = 0
    output = []
    chapter = None
    checkcounter = 0
    checkdata = {}

    if f"{type(moveset_file)}" == "<class 'str'>":  # Checks if the given type is a string or not
        moveset_file = moveset_file.split("\n")  # Turns it into a compatible string, line by line.

    divider = "+-"
    for numbr, line in enumerate(moveset_file):  # Starts to loop through the file

        line = line.removesuffix("\n")  # To make sure, as sometimes line will still have it.

        if dividers == 9:
            dividers = 1
            output.append(datadict)
            datadict = {
                "name": "",
                "general": {
                    "raw_count": None,
                    "avg_weight": None,
                    "viability_ceiling": None},
                "abilities": [],
                "items": [],
                "spreads": [],
                "moves": [],
                "teammates": [],
                "checks_and_counters": []
            }
            chapter = "name"
            # This is the last divider of a single pokémon's data. Resets base datadict platform and appends output to list.

        elif line.__contains__(divider):
            dividers += 1
            # If the line is a divider, adds one then continues

        else:
            # Chapter setter.
            # Chapters determine how the line is taken apart. Could have probs been done better, but it works.
            if dividers == 1:
                chapter = "name"
            elif dividers == 2:
                chapter = "general"
            elif dividers == 3:
                chapter = "abilities"
            elif dividers == 4:
                chapter = "items"
            elif dividers == 5:
                chapter = "spreads"
            elif dividers == 6:
                chapter = "moves"
            elif dividers == 7:
                chapter = "teammates"
            elif dividers == 8:
                chapter = "checks_and_counters"

            # Start taking the lines apart and adding their content to the right (sub)keys
            if chapter == "name":
                datadict["name"] = line.replace("|", "").replace(" ", "")  # There is only 1 line of name. Just adds it to the dict

            elif chapter == "general":
                split_line = line.split("| ")[1].split(": ")
                value = float(split_line[1].replace(" ", "").replace("|", ""))  # To prevent doing the same modifications repeatedly
                if float_int(value):
                    datadict["general"][split_line[0].replace(" ", "_").replace(".", "").lower()] = int(value)
                else:
                    datadict["general"][split_line[0].replace(" ", "_").replace(".", "").lower()] = value

            elif chapter == "abilities":
                if not line.lower().__contains__("| abilities") and not line.lower().__contains__("| items"):  # It needs to skip this line
                    split_line = raw_line_splitter(line)  # This is a repeated prodedure to take the line apart.
                    datadict["abilities"].append(
                        {
                            "name": " ".join(split_line[:-1]).lower(),
                            "usage": float(split_line[-1])
                        }
                    )  # Add the dict to the list.
            elif chapter == "items":
                if not line.lower().__contains__("| items") and not line.lower().__contains__("| spreads"):
                    split_line = raw_line_splitter(line)
                    datadict["items"].append(
                        {
                            "name": " ".join(split_line[:-1]),
                            "usage": float(split_line[-1])
                        }
                    )

            elif chapter == "spreads":
                if not line.lower().__contains__("| spreads") and not line.lower().__contains__("| moves"):
                    if not line.lower().__contains__("other"):
                        split_line = raw_line_splitter(line)

                        evs = split_line[0].split(":")[1].split("/")
                        datadict["spreads"].append(
                            {
                                "nature": split_line[0].split(":")[0].lower(),
                                "evs": {
                                    "health": int(evs[0]),
                                    "attack": int(evs[1]),
                                    "defense": int(evs[2]),
                                    "special-attack": int(evs[3]),
                                    "special-defense": int(evs[4]),
                                    "speed": int(evs[5])},
                                "usage": float(split_line[1])
                            }
                        )

            elif chapter == "moves":
                if not line.lower().__contains__("| moves") and not line.lower().__contains__("| teammates"):
                    split_line = raw_line_splitter(line)
                    datadict["moves"].append(
                        {
                            "name": " ".join(split_line[:-1]),
                            "usage": float(split_line[-1])
                        }
                    )

            elif chapter == "teammates":
                if not line.lower().__contains__("| teammates") and not line.lower().__contains__("| checks and counters"):
                    split_line = raw_line_splitter(line)
                    datadict["teammates"].append(
                        {
                            "name": " ".join(split_line[:-1]),
                            "usage": float(split_line[-1])
                        }
                    )

            elif chapter == "checks_and_counters":
                if not line.lower().__contains__("| checks and counters"):
                    checkcounter += 1
                    if checkcounter == 1:  # This is the first half of the check's entry
                        container = []
                        split_line = raw_line_splitter(line)
                        for entry in line.split():
                            if entry.__contains__("±"):
                                container = entry.split("±")  # gets the weird +- container out of there
                        checkdata = {
                            "name": split_line[0],
                            "effectiveness": float(container[0].removeprefix("(")),
                            "effectiveness_offset": float(container[1].removesuffix(")")),
                            "unknown_statistic": float(split_line[1])
                        }  # This is a temporary instance of this dict.
                    elif checkcounter == 2:  # This is the second half of the check's entry
                        checkcounter = 0
                        split_line = []
                        raw_split_line = line.split()  # Slightly different splitting procedure.
                        for entry in raw_split_line:
                            if entry.__contains__("%"):
                                split_line.append(entry)

                        checkdata["ko"] = float(split_line[0].removeprefix("(").replace("%", ""))  # Add data to the previously started instance.
                        checkdata["switched_out"] = float(split_line[1].replace("%", ""))

                        datadict["checks_and_counters"].append(checkdata)  # Add the data, then reset the instance to default.
                        checkdata = {}

    output.append(datadict)  # If it's the last mon of the file, dividers == 9 will not be called and thus would never be appended. This does that.
    return output


# Example dictionary
data_template = [
    {
        "name": str,
        "general":
            {
                "raw_count": int,
                "average_weight": float,
                "viability_ceiling": int
            },
        "abilities": [
            {
                "name": str,
                "usage": float
            }],
        "items": [
            {
                "name": str,
                "usage": float
            }],
        "spreads": [
            {
                "nature": str,
                "evs": {
                    "health": int,
                    "attack": int,
                    "defense": int,
                    "special-attack": int,
                    "special-defense": int,
                    "speed": int
                },
                "usage": float
            }],
        "moves": [
            {
                "name": str,
                "usage": float
            }],
        "teammates": [
            {
                "name": str,
                "usage": float
            }],
        "checks_and_counters": [
            {
                "name": str,
                "effectiveness": float,
                "effectiveness_offset": float,
                "unknown_statistic": float,
                "ko": float,
                "switched_out": float
            }]
    }
]

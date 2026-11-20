#!/usr/bin/env python3
"""Build a separate League-Soccer database with a playable parody club."""

import argparse
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring


# Speed, shooting, passing, dribbling, defending, physical, stamina.
STARS = (
    ("Enzo", "Khalifa", "CM", (74, 74, 92, 82, 77, 76, 91)),
    ("Lamine", "Pas Mal", "LM", (94, 78, 80, 93, 38, 62, 85)),
    ("Lionel", "Pessi", "AM", (87, 92, 93, 97, 36, 65, 76)),
    ("Cristiano", "Gronaldo", "CF", (90, 97, 77, 86, 40, 89, 87)),
)
STARTERS = (
    ("Nico", "Sans Filet", "GK"),
    ("Hugo", "Touche", "LB"),
    ("Axel", "Béton", "CB"),
    ("Samir", "Dégage", "CB"),
    ("Milo", "En Retard", "RB"),
    STARS[0],
    ("Adam", "Deux Touches", "CM"),
    STARS[1],
    STARS[2],
    ("Tao", "Sur La Ligne", "RM"),
    STARS[3],
)
BENCH = (
    ("Noé", "Gants Troués", "GK"),
    ("Léo", "Pied Carré", "CB"),
    ("Idris", "Tacle Propre", "RB"),
    ("Arthur", "Mi-Temps", "CM"),
    ("Bilal", "Sans GPS", "AM"),
    ("Rayan", "Tout Droit", "RM"),
    ("Sami", "Poteau", "CF"),
)
ROLE_RATINGS = {
    "GK": (52, 32, 58, 47, 72, 75, 67),
    "LB": (77, 49, 65, 62, 72, 70, 83),
    "CB": (62, 41, 59, 53, 82, 82, 76),
    "RB": (78, 52, 67, 64, 73, 68, 80),
    "CM": (67, 62, 79, 72, 69, 72, 80),
    "RM": (81, 62, 71, 76, 53, 63, 77),
    "AM": (72, 70, 77, 79, 50, 63, 74),
    "CF": (79, 78, 61, 73, 41, 77, 73),
}


def match_profile(ratings):
    speed, shooting, passing, dribbling, defending, physical, stamina = ratings
    skills = {
        "physical_balance": physical,
        "physical_reaction": (speed + defending + 75) / 3,
        "physical_acceleration": speed,
        "physical_velocity": speed,
        "physical_stamina": stamina,
        "physical_agility": (speed + dribbling) / 2,
        "physical_shotpower": shooting,
        "technical_standingtackle": defending,
        "technical_slidingtackle": defending - 4,
        "technical_ballcontrol": dribbling,
        "technical_dribble": dribbling,
        "technical_shortpass": passing,
        "technical_highpass": passing - 4,
        "technical_header": (shooting + physical) / 2,
        "technical_shot": shooting,
        "technical_volley": shooting - 3,
        "mental_calmness": (passing + dribbling) / 2,
        "mental_workrate": stamina,
        "mental_resilience": physical,
        "mental_defensivepositioning": defending,
        "mental_offensivepositioning": (shooting + dribbling) / 2,
        "mental_vision": passing,
    }
    average = sum(skills.values()) / len(skills)
    # At age 27, CalculateStat multiplies the normalized profile by 2.4 * base_stat.
    # This gives PlayerData the authored ratings before match condition and fatigue.
    profile = Element("profile")
    for key, skill in skills.items():
        SubElement(profile, key).text = f"{skill / (2 * average):.8f}"
    return average / 120, "\n".join(tostring(stat, encoding="unicode") for stat in profile)


def seed(connection):
    template = connection.execute(
        "SELECT l.country_id, t.formation_factory_xml, t.tactics_factory_xml "
        "FROM teams t JOIN leagues l ON l.id = t.league_id WHERE t.shortname = ?",
        ("AJA",),
    ).fetchone()
    if template is None:
        raise ValueError("The stock Ajax formation template is missing from the source database.")
    country, formation, tactics = template
    league = connection.execute(
        "INSERT INTO leagues (country_id, name, logo_url) VALUES (?, ?, ?)",
        (country, "Parodie", "images_competitions/parodie.png"),
    ).lastrowid
    team = connection.execute(
        "INSERT INTO teams (league_id, name, shortname, logo_url, kit_url, color1, color2, "
        "formation_xml, formation_factory_xml, tactics_xml, tactics_factory_xml) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            league, "FC Hors-jeu", "HJE", "images_teams/parodie/fc_hors_jeu.png", "",
            "239, 246, 232", "31, 53, 37", formation, formation, tactics, tactics,
        ),
    ).lastrowid

    for order, (first, last, role, *custom) in enumerate(STARTERS + BENCH):
        base_stat, profile = match_profile(custom[0] if custom else ROLE_RATINGS[role])
        connection.execute(
            "INSERT INTO players (team_id, nationalteam_id, firstname, lastname, role, age, "
            "base_stat, profile_xml, skincolor, hairstyle, haircolor, height, weight, "
            "formationorder, nationalteamformationorder) "
            "VALUES (?, NULL, ?, ?, ?, 27, ?, ?, ?, 'short01', 'darkblonde', ?, 74, ?, -1)",
            (team, first, last, role, base_stat, profile, 1 + order % 4,
             1.9 if role == "GK" else 1.75 + 0.035 * (order % 4), order),
        )


def build_database(source, destination):
    if source.resolve() == destination.resolve():
        raise ValueError("The source and destination must be different files.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        copy = Path(temporary) / destination.name
        with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as original:
            with closing(sqlite3.connect(copy)) as database:
                original.backup(database)
                with database:
                    seed(database)
        copy.replace(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    build_database(arguments.source, arguments.destination)


if __name__ == "__main__":
    main()

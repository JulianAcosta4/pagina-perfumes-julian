from app import app
from models import db, Perfume

# Mapeo completo: nombre exacto en BD → archivo de imagen en static/img/
IMAGENES = {

    # ── TESTER ────────────────────────────────────────────────
    "Toy Boy Moschino Tester 100ml":                  "toy_boy_moschino.jpg",
    "Blue Jeans Tester 75ml":                         "blue_jeans_versace.jpg",
    "Sauvage Dior EDP 100ml Tester":                  "sauvage_dior.jpg",          # subir foto
    "Polo Red Parfum Tester 100ml":                   "polo_red_parfum.jpg",
    "Scandal Absolu Tester 100ml":                    "scandal_absolu.jpg",
    "Versace Eros Najim Parfum Tester 100ml":         "versace_eros_najim.jpg",
    "Terre D'Hermes H24 Herbes Vives Tester 100ml":   "terre_hermes_h24.jpg",
    "Carolina Herrera Bad Boy Extreme EDP Tester 100ml": "carolina_herrera_bad_boy.jpg",
    "Acqua Di Gio Parfum Tester 100ml":               "acqua_di_gio.jpg",          # subir foto
    "La Nuit YSL Tester 100ml":                       "la_nuit_ysl.jpg",           # subir foto
    "Gentleman Givenchy Reserve Privée Tester 100ml": "gentleman_givenchy.jpg",
    "Guerlain Habit Rouge Tester 100ml":              "guerlain_habit_rouge.jpg",  # subir foto
    "Guerlain L'Homme Ideal Tester 100ml":            "guerlain_lhomme_ideal.jpg",
    "Terre D'Hermes Tester 100ml":                    "terre_hermes_h24.jpg",
    "Azzaro Forever Wanted Elixir Tester 100ml":      "azzaro_forever_wanted_elixir.jpg",
    "One Million Elixir 100ml":                       "one_million_elixir.jpg",
    "Dolce & Gabbana The One Tester 100ml":           "dg_the_one.jpg",
    "Dolce & Gabbana K Tester 100ml":                 "dg_k.jpg",
    "Naxos Xerjoff Tester 100ml":                     "naxos_xerjoff.jpg",
    "Naxos Erba Gold Tester 100ml":                   "naxos_xerjoff.jpg",
    "Montale Paris Tester 100ml":                     "montale_paris_tester.jpg",
    "Mancera Wild Leather Tester 100ml":              "mancera_wild_leather.jpg",
    "Montale Paris Boise Fruite Tester 100ml":        "montale_boise_fruite.jpg",

    # ── DISEÑADOR ─────────────────────────────────────────────
    "Ferrari 200ml":                                  "ferrari.jpg",               # subir foto
    "Calvin Klein Be 100ml Sellado":                  "ck_be.jpg",
    "CK Be 100ml":                                    "ck_be.jpg",
    "Burberry Hero Sellado 100ml":                    "burberry_hero2.jpg",
    "Kenzo Home 100ml":                               "issey_miyake_leau.jpg",
    "Invictus Parfum Sellado 200ml":                  "invictus_parfum.jpg",
    "Kit Kenzo Homme EDT 110ml + Gel Sellado":        "kit_kenzo_homme.jpg",
    "Polo 67 Eau de Parfum Sellado 125ml":            "polo_67.jpg",
    "Calvin Klein One Sellado 200ml":                 "ck_one.jpg",
    "Le Beau Le Parfum Sellado 125ml":                "le_beau_le_parfum.jpg",
    "Azzaro The Most Wanted Intense Sellado 100ml":   "azzaro_most_wanted.jpg",    # subir foto
    "Azzaro The Most Wanted Parfum Sellado 100ml":    "azzaro_most_wanted.jpg",    # subir foto
    "Valentino Uomo Born in Roma Sellado 100ml":      "valentino_born_in_roma.jpg",
    "Stronger With You Sellado 100ml":                "stronger_with_you.jpg",

    # ── NICHO ─────────────────────────────────────────────────
    "Mancera Cedrat Boise 120ml":                     "mancera_cedrat_boise.jpg",
    "Mancera Instant Crush 120ml":                    "mancera_instant_crush.jpg",
    "Montale Arabians Tonka 100ml":                   "montale_arabians_tonka.jpg",

    # ── ARABES ────────────────────────────────────────────────
    "Hawas Malibu 100ml":                             "hawas_malibu.jpg",
    "Hawas Ice 100ml":                                "hawas_ice.jpg",
    "Reyna 100ml":                                    "reyna.jpg",
    "Qaed Al Fursan 90ml":                            "qaed_al_fursan.jpg",
    "Yara Candid 100ml":                              "yara_candid.jpg",
    "Yara Tous 100ml":                                "yara_candy.jpg",
    "Yara Rosa 100ml":                                "yara_candid.jpg",
    "Shaheen Gold 100ml":                             "shaheen_gold.jpg",
    "Asad Bourbon 100ml":                             "asad_bourbon.jpg",
    "Khamrah 100ml":                                  "khamrah.jpg",
    "9AM Dive 100ml":                                 "9am_dive.jpg",
    "Club de Nuit Untold 105ml":                      "club_de_nuit_untold.jpg",
    "9PM 100ml":                                      "9pm.jpg",
    "The Kingdom 100ml":                              "the_kingdom.jpg",
    "Ebene 100ml":                                    "ebene.jpg",
    "Sceptre 100ml":                                  "sceptre_malachite.jpg",
    "Sublime 100ml":                                  "sublime_lattafa.jpg",
    "Philos Pura 100ml":                              "philos_pura.jpg",
    "Bareek 100ml":                                   "bareek.jpg",
    "Maison Alhambra Salvo 100ml":                    "maison_alhambra_salvo.jpg",
}

with app.app_context():
    actualizados = 0
    sin_imagen   = 0

    for nombre, imagen in IMAGENES.items():
        perfume = Perfume.query.filter_by(nombre=nombre).first()
        if perfume:
            perfume.imagen = imagen
            actualizados += 1
        else:
            print(f"  ⚠️  No encontrado en BD: {nombre}")

    db.session.commit()

    # Mostrar cuántos quedaron sin imagen
    sin = Perfume.query.filter(Perfume.imagen == None).count()

    print(f"\n✅ {actualizados} perfumes actualizados con imagen.")
    print(f"📷 {sin} perfumes todavía sin imagen (podés agregarlas desde el panel admin).")
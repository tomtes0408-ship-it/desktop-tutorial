# -*- coding: utf-8 -*-
"""ציטוט מילולי מן המקור לכל הערת שוליים בעבודה.

המפתח הוא מספר ההערה בעבודה. הערך הוא רשימה של שלישיות:
    (מזהה מקור, לוקטור, ציטוט מילולי)

מזהי מקור:  huguen / kopf / gunes / royden
לוקטור:     מספר עמוד מודפס אצל huguen ו-gunes; מספר פסקה (AGU) אצל
            kopf ו-royden; המחרוזת "fig1a" לכיתוב איור 1a אצל kopf.

הציטוטים הועתקו מן ה-PDF עצמם. build_verification.py מאמת כל אחד מהם
מול העמוד או הפסקה שהלוקטור טוען לו, ונכשל אם אינו נמצא שם.
"""



# הערות שהן ייחוס מקור של איור - אין להן טענה לאמת
ATTRIBUTION = {
    28: "ייחוס מקור לאיור 1 (Wikimedia Commons, CC BY-SA 3.0).",
    43: "ייחוס מקור לאיור 2 (Güneş et al. 2018, איור 21, עמ' 315).",
    54: "ייחוס מקור לאיור 3 (Huguen et al. 2006, איור 4, עמ' 65).",
}

QUOTES = {
 1: [
("huguen", 61,
      "which results from the relatively rapid (>3 cm/year) subduction of "
      "the African plate beneath eastern Europe")
],
 2: [
("huguen", 61,
      "The Eastern Mediterranean Sea is a remnant of a deep Mesozoic "
      "oceanic basin, now almost totally consumed as a result of "
      "long-term plate convergence between Eurasia and Africa.")
],
 3: [
("huguen", 62,
      "and surrounding the foot of Peloponnesus, Crete and Rhodes islands "
      "continental slopes")
],
 4: [
("huguen", 61,
      "a large, arc-shaped, sedimentary wedge, more than 1500 km long and "
      "200-250 km wide, known as the Mediterranean Ridge")
],
 5: [
("kopf", 2,
      "It has been demonstrated to be the fastest outward growing wedge "
      "in most recent Earth history, with a rate of up to 10 km Myr1 "
      "[Kastens, 1991].")
],
 6: [
("huguen", 61,
      "The Mediterranean Ridge, which consists of a thick pile (up to 12 "
      "km) of offscrapped and stacked sediments")
],
 7: [
("kopf", 1,
      "The onset of accretion coincides with exhumation of thrust sheets "
      "(19 Ma), followed by rapid sediment accretion with thick, "
      "evaporite-bearing incoming successions facilitating outward growth "
      "of the wedge.")
],
 8: [
("huguen", 61,
      "partly because it contains, in its upper sedimentary cover, thick "
      "Upper Miocene/Messinian evaporitic sequences (locally up to 2 km)")
],
 9: [
("huguen", 73,
      "and finally a complex distribution, within parts of its cover, of "
      "thick ductile sedimentary layers (i.e. Messinian evaporites)")
],
 10: [
("kopf", "fig1a",
      "Crete is a forearc topographic high, which earlier acted as the "
      "backstop to allow accretion of the Mediterranean Ridge (light "
      "shading).")
],
 11: [
("huguen", 61,
      "a unique regional kinematics, controlled by frontal convergence "
      "south of Crete (central Mediterranean Ridge) and oblique "
      "subduction with opposite sense of shear for the western (Ionian) "
      "and eastern (Levantine) domains of the Mediterranean Ridge")
],
 12: [
("royden", 7,
      "GPS data indicate a convergence rate of ~35 mm/yr across the "
      "southern Hellenides, as measured between Africa and points in the "
      "overriding (Aegean) domain")
],
 13: [
("royden", 1,
      "a rapidly subducting Ionian oceanic lithosphere in the south (~35 "
      "mm/yr)")
],
 14: [
("royden", 1,
      "the active Hellenic subduction front is dextrally offset by "
      "100-120 km across the Kephalonia Transform Zone")
],
 15: [
("huguen", 62,
      "the Mediterranean Ridge is bathymetrically bounded by a series of "
      "disconnected and deep troughs (Matapan, Pliny, Strabo Trenches, "
      "Rhodes Trough), ranging in depth from 5000 to 3000 m")
],
 16: [
("huguen", 62,
      "the Mediterranean Ridge faces discontinuous segments of abyssal "
      "plains whose water depths range between 4000 m (Ionian Abyssal "
      "Plain) to 3100 m (Herodotus Abyssal Plain at the base of the "
      "Egyptian margin)")
],
 17: [
("kopf", 5,
      "the present-day Hellenic Trench is not a deep-sea trench in the "
      "strictest sense, but a forearc depression with very little "
      "sedimentary infill")
],
 18: [
("kopf", 5,
      "However, with ongoing accretion in the Plio-Quaternary this "
      "deformation front migrated southward")
],
 19: [
("huguen", 73,
      "Both trenches are composed of successive wide and partly "
      "sedimented basins, en echelon arranged, and clearly representative "
      "of left lateral strike-slip movement.")
],
 20: [
("huguen", 72,
      "Between these two trenches, the backstop area is composed of: a "
      "plateau-like area, slightly sloping northwards, and characterized "
      "by large lobe-like features, interpreted as gravity induced "
      "deformation (Mascle et al., 1999), and the Strabo Seamounts, a "
      "series of massive bathymetric highs trending in a general N60 "
      "direction, rifted from the Cretan margin")
],
 21: [
("huguen", 73,
      "Along the eastern branch, shearing is also mainly restricted to "
      "the boundary between the Cretan margin and the backstop area "
      "(Pliny Trench) and the contact between the Strabo Mountains and "
      "the Mediterranean Ridge Inner domain (Strabo Trench).")
],
 22: [
("huguen", 66,
      "a northern area in tectonic backthrust contact with a flat inner "
      "region extending just south of the deep troughs (Matapan Trench) "
      "that run at the base of the Aegean continental slope")
],
 23: [
("huguen", 62,
      "with only a very narrow, flat-bottomed furrow (water depth "
      "averaging 2800 m) north of the steep Libyan continental slope")
],
 24: [
("huguen", 66,
      "The deep eastern Mediterranean basin is characterized by three "
      "conspicuous morphologic features - besides the Mediterranean Ridge "
      "proper - which represents the major morphologic relief.")
],
 25: [
("huguen", 61,
      "During the last decade this tectono-sedimentary accretionary "
      "prism, which results from the Hellenic subduction, has been "
      "intensively surveyed by swath mapping, multichannel seismic "
      "profiling and deep dives.")
],
 26: [
("huguen", 66,
      "Its summit, just north of Cyrenaica (Antaeus High, Figure 2), "
      "reaches water depth of less than 1250 m, while its Ionian and "
      "Levantine branches extend into water depths of approximately "
      "respectively 3200 and 2200 m")
],
 27: [
("huguen", 66,
      "It reaches its maximum width, about 200 km, facing the deep Ionian "
      "Abyssal Plain. Between central Crete and Libya, the ridge appears "
      "much narrower, with an average width of only 130 km.")
],
 29: [
("huguen", 66,
      "Truffert (1992) identified, on the base of the deformational "
      "pattern, three different morphostructural provinces: an outer "
      "folded front, an almost flat central province, and a northern area "
      "in tectonic backthrust contact with a flat inner region")
],
 30: [
("huguen", 66,
      "Comparable morphostructural domains, showing local variations, "
      "have been recognized within the central and Levantine "
      "Mediterranean Ridge branches")
],
 31: [
("huguen", 73,
      "Folds are tight where evaporites are thin, in particular between "
      "Crete and Libya where little space is available for the wedge to "
      "grow, and they progressively widen towards the Levantine and "
      "Ionian branches of the Mediterranean Ridge due to both thickening "
      "of the evaporitic layers")
],
 32: [
("huguen", 67,
      "the Mediterranean Ridge Hellenic backstop (Figures 3 and 4), "
      "acting as a mechanical ''buttress'' of complex shape")
],
 33: [
("huguen", 69,
      "This backstop not only extends far south of the Hellenic Trenches, "
      "but its southern edge also has a complex ''W'' shape")
],
 34: [
("huguen", 69,
      "These ridge units are systematically thrusted over the backstop, "
      "with clear evidence for dextral shearing")
],
 35: [
("kopf", 6,
      "The entire prism is thrust onto the Libyan Margin to the south, "
      "and backthrust over the Cretan Margin to the north [Mascle et al., "
      "1999].")
],
 36: [
("kopf", 1,
      "Depth migration of seismic reflection profiles across the "
      "Mediterranean Ridge accretionary complex between the African and "
      "Eurasian blocks illustrates profound variations in the geometry "
      "and internal structure along strike. Structural interpretations of "
      "four cross sections, together with bathymetric and acoustic "
      "surface information and drilling data, are used to volumetrically "
      "balance the amount of subduction versus accretion with time.")
],
 37: [
("kopf", 1,
      "Results suggest the existence of three distinct scenarios, with a "
      "jump in decollement in the west, intense backthrusting in the "
      "central part between Libya and Crete, and transcurrent tectonism "
      "in the east.")
],
 38: [
("kopf", 1,
      "The minimum rate of accretion (20-25% of the total sediment "
      "supply) is observed in the central portion where the ridge suffers "
      "maximum deformation. Here the indenting leading edge of the "
      "African Plate apparently forces the sediment into subduction, or "
      "local underplating.")
],
 39: [
("kopf", 2,
      "It has been demonstrated to be the fastest outward growing wedge "
      "in most recent Earth history, with a rate of up to 10 km Myr1 "
      "[Kastens, 1991].")
],
 40: [
("kopf", 42,
      "In contrast, the easternmost subduction flux of almost 50 km3 km1 "
      "Myr1 (line 30) range at the upper limit of material transfer on a "
      "global scale.")
],
 41: [
("huguen", 72,
      "This fold belt is made of salt-rooted anticline-synclines "
      "developing above a decollement level, which correlates with the "
      "base of Messinian evaporites")
],
 42: [
("huguen", 71,
      "The Messinian wedge (i.e. the portion of the wedge that "
      "incorporates Messinian evaporites originally deposited in the "
      "subduction trough) does not exceed 80 km in width.")
],
 44: [
("huguen", 72,
      "Within the axial domain no evaporites layers of significant extend "
      "have been found (Kopf et al., 2003), resulting in a different "
      "morphostructural pattern")
],
 45: [
("huguen", 61,
      "particularities of its sedimentary cover, which includes massive "
      "salt layers within the outer Mediterranean Ridge and local salt "
      "deposits within the inner domains, that control the north-south "
      "morphostructural variability of the sedimentary wedge")
],
 46: [
("huguen", 66,
      "Based on sampling and/or direct in situ observations several of "
      "these features have been interpreted as mud volcanoes through "
      "which massive mud flows, fluids and brines are emitted on the sea "
      "floor")
],
 47: [
("huguen", 69,
      "Mud volcanoes of all size punctuate the entire region (Figure 3), "
      "with 95% of them located at proximity of the prism/backstop "
      "contact")
],
 48: [
("huguen", 71,
      "an area of the Mediterranean Ridge where the now well-known Olimpi "
      "and United Nations mud volcano fields (Figure 6) have previously "
      "been detected (Cita et al., 1981) and intensively surveyed during "
      "PRISMED 2")
],
 49: [
("huguen", 73,
      "shearing is presently localized at the geological contact between "
      "the ridge and its backstop, thus interpreted as a major dextral, "
      "compressive flower structure, as well as a preferential site for "
      "massive mud eruption")
],
 50: [
("huguen", 69,
      "resulting into an extraordinary salt tectonics including "
      "sub-circular salt lobes (e.g. 35 N-22 E) with tight gravity "
      "folding and ''rafts'' of Plio-Quaternary.")
],
 51: [
("huguen", 72,
      "The sedimentary cover of this last area is in fact progressively "
      "gliding northward and filling the series of deep troughs that "
      "constitute the Pliny Trench at the foot of the Cretan continental "
      "slope.")
],
 52: [
("huguen", 72,
      "this folded belt is cut by a dense set of conjugate faults, "
      "probably strike-slip faults, either triggered by southwards "
      "progressive spreading of the salt-rich and ductile superficial "
      "cover")
],
 53: [
("huguen", 73,
      "The flat and deeper backstop area shows well expressed northward "
      "gliding deformations over the entire studied area")
],
 55: [
("huguen", 73,
      "and finally a complex distribution, within parts of its cover, of "
      "thick ductile sedimentary layers (i.e. Messinian evaporites)")
],
 56: [
("royden", 1,
      "Consistency between geodynamic model results and geologic "
      "observations suggest that the middle Miocene and younger "
      "deformation of the Hellenic upper plate, including formation of "
      "the Central Hellenic Shear Zone, can be quantitatively understood "
      "as the result of spatial variations in the buoyancy of the "
      "subducting slab.")
],
 57: [
("royden", 38,
      "The model time at which the northern Hellenic and Peloponnesus "
      "trenches begin to separate is ~6-8 Ma, with most of the model "
      "trench separation occurring after 5 Ma.")
],
 58: [
("kopf", 42,
      "In contrast, the easternmost subduction flux of almost 50 km3 km1 "
      "Myr1 (line 30) range at the upper limit of material transfer on a "
      "global scale.")
],
 59: [
("huguen", 62,
      "the Mediterranean Ridge is bathymetrically bounded by a series of "
      "disconnected and deep troughs (Matapan, Pliny, Strabo Trenches, "
      "Rhodes Trough)"),
("kopf", 5,
      "What is usually referred to as the Hellenic Trench, or Hellenic "
      "Trough (Figure 1a), represented the deformation front of the "
      "initial MedRidge during the early Miocene. However, with ongoing "
      "accretion in the Plio-Quaternary this deformation front migrated "
      "southward, so that the present-day Hellenic Trench is not a "
      "deep-sea trench in the strictest sense, but a forearc depression "
      "with very little sedimentary infill")
],
 60: [
("royden", 1,
      "coinciding with the junction of a slowly subducting Adriatic "
      "continental lithosphere in the north (5-10 mm/yr) and a rapidly "
      "subducting Ionian oceanic lithosphere in the south (~35 mm/yr)")
],
 61: [
("huguen", 73,
      "interpreted as the result of ductile salt tectonics related to the "
      "presence of evaporite layers, deposited within a pre-existing "
      "fore-arc basin setting and acting as a passive decollement level")
],
}

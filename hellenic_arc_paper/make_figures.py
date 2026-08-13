# -*- coding: utf-8 -*-
"""יוצר את שני האיורים הסכמטיים לעבודת הסיכום על הקשת ההלנית.

הפלט:
    figure1_map.png            - מפה סכמטית של הקשת ההלנית
    figure2_cross_section.png  - חתך רוחב סכמטי דרום-צפון

הערה: matplotlib אינו מיישם את אלגוריתם ה-bidi, ולכן כל מחרוזת עברית עוברת
דרך get_display לפני הציור.
"""

import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from bidi.algorithm import get_display
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, FancyArrow, Patch, Polygon

plt.rcParams["font.family"] = "DejaVu Sans"

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

C_LAND = "#e4dbc7"
C_SEA = "#eef4f9"
C_RIDGE = "#c2a86a"
C_TROUGH = "#1f4e79"
C_FRONT = "#9c3025"
C_SALT = "#e8cf72"
C_WEDGE = "#cbb68d"
C_INCOMING = "#ddd3bb"
C_PRESALT = "#b3c3ac"
C_CRUST = "#8ea2ac"
C_MANTLE = "#9a8b7c"
C_UPPER = "#9fa9a3"


def he(text):
    """מחזיר מחרוזת מסודרת לתצוגה מימין לשמאל."""
    return get_display(text, base_dir="R")


def arc(center, radius, theta_start, theta_end, n=400):
    theta = np.radians(np.linspace(theta_start, theta_end, n))
    return center[0] + radius * np.cos(theta), center[1] + radius * np.sin(theta)


def label(ax, x, y, txt, size=9, color="#333333", rot=0, alpha=0.72, ha="center"):
    ax.text(x, y, he(txt), fontsize=size, color=color, ha=ha, va="center",
            rotation=rot, zorder=8,
            bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none",
                      alpha=alpha))


def make_map():
    fig, ax = plt.subplots(figsize=(9.2, 6.4))
    ax.set_facecolor(C_SEA)

    center = (24.0, 40.6)

    # --- רצועת רכס הים התיכון (מנסרת ההצטברות) ---
    x_out, y_out = arc(center, 8.5, 212, 328)
    x_in, y_in = arc(center, 6.35, 212, 328)
    band = np.concatenate([np.stack([x_out, y_out], axis=1),
                           np.stack([x_in[::-1], y_in[::-1]], axis=1)])
    ax.add_patch(Polygon(band, closed=True, facecolor=C_RIDGE, alpha=0.85,
                         edgecolor="#a58c50", lw=0.6, zorder=1))

    # --- יבשות (סכמטי בלבד) ---
    for pts in [
        [(19.4, 40.5), (23.6, 40.5), (24.5, 39.0), (23.2, 37.9), (21.2, 37.0),
         (20.3, 38.4), (19.4, 39.4)],                                   # יוון
        [(26.4, 40.5), (31.6, 40.5), (31.6, 36.5), (29.6, 36.2),
         (27.2, 37.2), (26.2, 38.6)],                                   # אנטוליה
        [(17.4, 30.6), (31.6, 30.6), (31.6, 32.3), (27.0, 32.0),
         (23.5, 32.8), (20.0, 32.5), (17.4, 32.1)],                     # אפריקה
    ]:
        ax.add_patch(Polygon(pts, closed=True, facecolor=C_LAND,
                             edgecolor="#9c9079", lw=0.9, zorder=3))

    ax.add_patch(Ellipse((24.9, 35.25), width=2.9, height=0.6, angle=-4,
                         facecolor=C_LAND, edgecolor="#9c9079", lw=0.9,
                         zorder=4))
    ax.add_patch(Ellipse((28.05, 36.25), width=0.8, height=0.42, angle=-35,
                         facecolor=C_LAND, edgecolor="#9c9079", lw=0.9,
                         zorder=4))

    # --- חזית העיוות ---
    ax.plot(x_out, y_out, color=C_FRONT, lw=2.2, zorder=5)
    for i in range(15, len(x_out) - 15, 28):
        dx, dy = x_out[i + 1] - x_out[i], y_out[i + 1] - y_out[i]
        n = np.hypot(dx, dy)
        ax.plot([x_out[i], x_out[i] + 0.24 * (-dy / n)],
                [y_out[i], y_out[i] + 0.24 * (dx / n)],
                color=C_FRONT, lw=1.7, zorder=5)

    # --- מערכת השקעים ההלניים ---
    x_tr, y_tr = arc(center, 6.0, 216, 324)
    ax.plot(x_tr, y_tr, color=C_TROUGH, lw=3.0, zorder=6)

    # Calypso Deep - על קו השקעים, דרומית-מערבית לפלופונס
    k = int(np.argmin(np.abs(x_tr - 21.6)))
    ax.plot(x_tr[k], y_tr[k], marker="v", ms=11, color="#12314f", zorder=7)

    # --- הרי בוץ על האגף הצפוני של הרכס ---
    mv_lon = np.array([24.3, 25.3, 26.2])
    mv_lat = np.array([34.25, 34.15, 34.3])
    ax.plot(mv_lon, mv_lat, marker="^", ls="none", ms=7, color="#6b4a1c",
            zorder=7)

    # --- חץ תנועת נוביה ---
    ax.add_patch(FancyArrow(23.0, 31.1, 0.0, 1.25, width=0.10, head_width=0.34,
                            head_length=0.4, color="#1f6b4a", zorder=7))

    label(ax, 20.9, 39.7, "יוון", 10, "#4a4331")
    label(ax, 29.6, 39.3, "אנטוליה", 10, "#4a4331")
    label(ax, 25.9, 38.4, "אגן האגאי", 10, "#4a4331")
    label(ax, 24.9, 35.25, "קרתה", 10, "#4a4331", rot=-4)
    label(ax, 28.9, 36.9, "רודוס", 8.5, "#4a4331")
    label(ax, 29.4, 31.2, "אפריקה (לוח נוביה)", 10, "#4a4331")
    label(ax, 24.9, 31.3, "תנועת נוביה, ~35 מ\"מ/שנה", 9, "#1f6b4a")
    label(ax, 21.0, 33.3, "רכס הים התיכון –\nמנסרת ההצטברות", 10, "#5a4715")
    label(ax, 25.4, 33.4, "הרי בוץ (שדה אולימפי)", 8.5, "#6b4a1c")

    ax.annotate(he("Calypso Deep\n(5,267 מ')"), xy=(x_tr[k], y_tr[k]),
                xytext=(18.9, 37.4), fontsize=8.5, color="#12314f",
                ha="center", va="center", zorder=8,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none",
                          alpha=0.85),
                arrowprops=dict(arrowstyle="-", color="#12314f", lw=1.0))

    for lon, lat, name in [(22.3, 35.8, "מטפאן/פטולמאוס"),
                           (25.4, 34.75, "פליני"),
                           (27.4, 35.15, "סטראבו")]:
        label(ax, lon, lat, name, 8, "#12314f", alpha=0.8)

    handles = [
        Line2D([], [], color=C_TROUGH, lw=3.0, label=he("השקעים ההלניים")),
        Line2D([], [], color=C_FRONT, lw=2.2, label=he("חזית העיוות")),
        Patch(facecolor=C_RIDGE, edgecolor="#a58c50", alpha=0.85,
              label=he("מנסרת ההצטברות")),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8.5, framealpha=0.9,
              borderpad=0.6).set_zorder(9)

    ax.set_xlim(17.4, 31.6)
    ax.set_ylim(30.6, 40.5)
    ax.set_aspect(1 / np.cos(np.radians(35.5)))
    ax.set_xlabel(he("אורך גיאוגרפי (מזרח)"), fontsize=9)
    ax.set_ylabel(he("רוחב גיאוגרפי (צפון)"), fontsize=9)
    ax.tick_params(labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#9aa5ab")

    fig.tight_layout()
    path = os.path.join(OUT_DIR, "figure1_map.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def make_cross_section():
    fig, ax = plt.subplots(figsize=(9.6, 5.2))

    x = np.linspace(0, 100, 900)
    XF = 15.0   # חזית העיוות
    XB = 64.0   # מגע המנסרה עם ה-backstop

    seabed = np.interp(x, [0, 15, 35, 55, 62, 70, 74, 80, 100],
                       [-4.1, -4.1, -3.3, -2.4, -4.6, -5.2, -4.0, -0.5, 0.4])
    decol = np.interp(x, [0, 15, 40, 55, 64, 80, 100],
                      [-5.1, -5.2, -7.2, -8.6, -9.6, -13.2, -17.2])
    salt_base = decol - np.interp(x, [0, 64, 100], [1.0, 0.7, 0.5])
    crust_top = salt_base - np.interp(x, [0, 64, 100], [3.0, 3.6, 4.0])
    crust_base = crust_top - 6.5

    ax.fill_between(x, seabed, 4.0, color="#dfeaf2", zorder=0)
    ax.fill_between(x, decol, seabed, where=(x <= XF), color=C_INCOMING,
                    zorder=1)
    ax.fill_between(x, decol, seabed, where=(x >= XF) & (x <= XB),
                    color=C_WEDGE, zorder=1)
    ax.fill_between(x, decol, seabed, where=(x >= XB), color=C_UPPER, zorder=1)
    ax.fill_between(x, salt_base, decol, color=C_SALT, hatch="xx",
                    edgecolor="#a58d2a", lw=0.4, zorder=2)
    ax.fill_between(x, crust_top, salt_base, color=C_PRESALT, zorder=1)
    ax.fill_between(x, crust_base, crust_top, color=C_CRUST, zorder=1)
    ax.fill_between(x, -28, crust_base, color=C_MANTLE, alpha=0.42, zorder=0)

    # העתקים הפוכים בתוך המנסרה
    for x0 in np.arange(19, XB - 3, 5.0):
        i = int(x0 / 100 * (len(x) - 1))
        j = int(min(x0 + 5.5, 99) / 100 * (len(x) - 1))
        ax.plot([x0, x0 + 5.5], [seabed[i], decol[j]], color="#7a5a24",
                lw=0.9, zorder=3)

    ax.plot(x, seabed, color="#2f3d45", lw=1.5, zorder=4)
    ax.plot(x, decol, color="#b03a2e", lw=2.4, zorder=4)
    ax.plot([XF, XF], [seabed[int(XF / 100 * 899)], 1.2], ls=":", lw=1.2,
            color="#b03a2e", zorder=4)
    ax.plot([XB, XB], [decol[int(XB / 100 * 899)], seabed[int(XB / 100 * 899)]],
            ls="--", lw=1.2, color="#5c5344", zorder=4)

    # הר בוץ ומסלול הנוזלים
    mv_i = int(45 / 100 * 899)
    ax.annotate("", xy=(45, seabed[mv_i] + 0.05), xytext=(39, decol[int(39 / 100 * 899)]),
                arrowprops=dict(arrowstyle="-|>", color="#1b6ca8", lw=1.9),
                zorder=5)
    ax.add_patch(Polygon([(42.2, seabed[mv_i]), (45, seabed[mv_i] + 1.05),
                          (47.8, seabed[mv_i])], closed=True,
                         facecolor="#7a4f22", edgecolor="#4d3115", lw=0.8,
                         zorder=6))

    ax.add_patch(FancyArrow(3, -19.8, 9, 1.0, width=0.32, head_width=1.2,
                            head_length=2.4, color="#1f6b4a", zorder=6))

    label(ax, 5, 2.9, "דרום", 10, "#2f3d45")
    label(ax, 95, 2.9, "צפון", 10, "#2f3d45")
    label(ax, 7.5, -2.0, "מישור תהומי\nוכיסוי סדימנטרי נכנס", 8.5, "#5a5343")
    label(ax, 15, 2.2, "חזית העיוות", 9, "#b03a2e")
    label(ax, 30, -0.6, "מנסרת ההצטברות (רכס הים התיכון)", 9.5, "#5a4715")
    label(ax, 45, 0.9, "הר בוץ", 8.5, "#4d3115")
    label(ax, 32, -4.9, "לחץ-יתר וזרימת נוזלים", 7.5, "#1b6ca8", alpha=0.8)
    label(ax, 60, -11.6, "סדימנטים טרום-מסיניים", 8.5, "#3f4f38")
    label(ax, 28, -13.9, "קרום לוח נוביה", 9, "#31424c")
    label(ax, 25, -22.0, "מעטפת הלוח השוקע", 8.5, "#4a4034")
    label(ax, 17, -19.2, "התכנסות", 8.5, "#1f6b4a")
    label(ax, 69, -3.4, "שקע הלני", 9, "#12314f")
    label(ax, 82, -6.0, "backstop – הלוח העליון", 8.5, "#3c4740")
    label(ax, 88, 2.2, "קרתה (רכס קדם-קשתי)", 9, "#4b4335")

    ax.annotate(he("מפלס ניתוק במלח המסיני"), xy=(33, -7.1), xytext=(28, -9.9),
                fontsize=9, color="#8a6d10", ha="center", va="center", zorder=8,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none",
                          alpha=0.8),
                arrowprops=dict(arrowstyle="-", color="#8a6d10", lw=1.0))

    ax.set_xlim(0, 100)
    ax.set_ylim(-26, 4)
    ax.set_xlabel(he("מרחק אופקי (סכמטי; רוחב המנסרה בפועל – מאות ק\"מ)"),
                  fontsize=9)
    ax.set_ylabel(he("עומק (ק\"מ, סכמטי)"), fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_yticks([-25, -20, -15, -10, -5, 0])
    for spine in ax.spines.values():
        spine.set_edgecolor("#9aa5ab")

    fig.tight_layout()
    path = os.path.join(OUT_DIR, "figure2_cross_section.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(make_map())
    print(make_cross_section())

import matplotlib.pyplot as plt

def default_autoclave_profile():
    return {
        "time_min": [0, 30, 90, 150, 210],
        "temp_C":  [20, 120, 180, 180, 50],
        "pressure_bar": [0, 3, 6, 6, 0],
    }

def plot_autoclave_profile(profile=None, show=True, ax=None):
    if profile is None:
        profile = default_autoclave_profile()

    t = profile["time_min"]
    T = profile["temp_C"]
    p = profile["pressure_bar"]

    if ax is None:
        fig, ax1 = plt.subplots()
    else:
        ax1 = ax

    ax1.plot(t, T, label="Temperatur (°C)")
    ax1.set_xlabel("Zeit [min]")
    ax1.set_ylabel("Temperatur [°C]")

    ax2 = ax1.twinx()
    ax2.plot(t, p, linestyle="--", label="Druck (bar)")
    ax2.set_ylabel("Druck [bar]")

    if show:
        plt.show()

    return ax1

from io import BytesIO

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt

from src.visualization.models import FigureArtifact


def line_figure(title: str, x: list[float], y: list[float]) -> FigureArtifact:
    if len(x) != len(y) or not x: raise ValueError("x and y must be non-empty and equal length")
    figure, axis=plt.subplots();axis.plot(x,y);axis.set_title(title);axis.set_xlabel("x");axis.set_ylabel("y")
    buffer=BytesIO();figure.savefig(buffer,format="svg",bbox_inches="tight");plt.close(figure)
    return FigureArtifact.from_svg(title,buffer.getvalue())

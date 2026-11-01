"""Animate NASA C-MAPSS measurements, with one panel per sensor.

Install: python3 -m pip install numpy matplotlib pillow imageio-ffmpeg
Run from the repository root: python3 video/plot_turbofan_video.py
Other engine: python3 video/plot_turbofan_video.py --engine 5 --sensors 2 4 7 11
Test split: python3 video/plot_turbofan_video.py --split test --engine 1
GIF: python3 video/plot_turbofan_video.py --output video/output/engine1.gif

Data time = engine operating cycle (cruise snapshot), not date or seconds.
FPS controls playback speed only. No true onset labels are provided.
Sensor metadata: Table 2 of Damage Propagation Modeling.pdf in CMAPSSData.zip.
"""
import argparse
import csv
import math
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
import numpy as np

ROOT = Path(__file__).resolve().parent
SENSOR_METADATA = {
    1: ('T2', 'Total temperature at fan inlet', 'deg R'),
    2: ('T24', 'Total temperature at LPC outlet', 'deg R'),
    3: ('T30', 'Total temperature at HPC outlet', 'deg R'),
    4: ('T50', 'Total temperature at LPT outlet', 'deg R'),
    5: ('P2', 'Pressure at fan inlet', 'psia'),
    6: ('P15', 'Total pressure in bypass duct', 'psia'),
    7: ('P30', 'Total pressure at HPC outlet', 'psia'),
    8: ('Nf', 'Physical fan speed', 'rpm'),
    9: ('Nc', 'Physical core speed', 'rpm'),
    10: ('epr', 'Engine pressure ratio (P50/P2)', 'dimensionless'),
    11: ('Ps30', 'Static pressure at HPC outlet', 'psia'),
    12: ('phi', 'Ratio of fuel flow to Ps30', '(lbm/s)/psi'),
    13: ('NRf', 'Corrected fan speed', 'rpm'),
    14: ('NRc', 'Corrected core speed', 'rpm'),
    15: ('BPR', 'Bypass ratio', 'dimensionless'),
    16: ('farB', 'Burner fuel-air ratio', 'dimensionless'),
    17: ('htBleed', 'Bleed enthalpy', 'not specified'),
    18: ('Nf_dmd', 'Demanded fan speed', 'rpm'),
    19: ('PCNfR_dmd', 'Demanded corrected fan speed', 'rpm'),
    20: ('W31', 'HPT coolant bleed', 'lbm/s'),
    21: ('W32', 'LPT coolant bleed', 'lbm/s'),
}


def trailing_mean(values, window):
    result = np.full(len(values), np.nan)
    if len(values) >= window:
        result[window-1:] = np.convolve(values, np.ones(window)/window, mode='valid')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--split', choices=['train', 'test'], default='train')
    parser.add_argument('--subset', choices=['FD001', 'FD002', 'FD003', 'FD004'], default='FD001')
    parser.add_argument('--engine', type=int, default=1)
    parser.add_argument('--sensors', type=int, nargs='+', default=[2, 4, 7, 11])
    parser.add_argument('--window', type=int, default=15)
    parser.add_argument('--fps', type=int, default=15)
    parser.add_argument('--step', type=int, default=1, help='Cycles advanced per frame')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.window < 1 or args.fps < 1 or args.step < 1:
        parser.error('window, fps and step must be positive')
    if not 1 <= len(args.sensors) <= 6 or any(s not in range(1,22) for s in args.sensors):
        parser.error('Choose between 1 and 6 sensors, each numbered 1–21')
    source = ROOT / 'csv' / args.subset / f'{args.split}.csv'
    if not source.exists():
        parser.error(f'Missing {source}. From the repository root, run python3 get_nasa_turbofan.py --subset {args.subset}.')
    with source.open() as stream:
        rows = [r for r in csv.DictReader(stream) if int(r['engine_id']) == args.engine]
    rows.sort(key=lambda r: int(r['cycle']))
    if not rows:
        parser.error(f'Engine {args.engine} is absent from {source.name}')
    metadata = SENSOR_METADATA
    cycles = np.array([int(r['cycle']) for r in rows])
    rul = np.array([int(r['rul']) for r in rows])
    ncols = 2 if len(args.sensors)>1 else 1
    nrows = math.ceil(len(args.sensors)/ncols)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'axes.spines.top':False,
                         'axes.spines.right':False, 'axes.titleweight':'bold'})
    fig, axes = plt.subplots(nrows,ncols,figsize=(13, 3.4*nrows+1.4),squeeze=False)
    fig.subplots_adjust(left=.09,right=.97,bottom=.16,top=.80,hspace=.48,wspace=.30)
    fig.suptitle(f'NASA {args.subset} · {args.split} engine {args.engine}',x=.09,y=.97,ha='left',fontsize=19,fontweight='bold')
    counter=fig.text(.09,.89,'',fontsize=12,color='#24445C')
    fig.text(.09,.065,'Data time: one engine operating cycle per snapshot. Playback speed has no physical-time meaning.',fontsize=10)
    fig.text(.09,.035,f'Light line: raw measurement. Dark line: trailing {args.window}-cycle mean. True degradation onset is not labeled.',fontsize=10)
    fig.text(.09,.008,'Retrospective view: fixed axes use the full record; displayed RUL is ground truth, not a prediction.',fontsize=9,color='#526271')
    panels=[]
    for ax,sensor in zip(axes.flat,args.sensors):
        symbol,description,unit=metadata[sensor]
        values=np.array([float(r[f'sensor_{sensor}']) for r in rows])
        smooth=trailing_mean(values,args.window)
        lo,hi=values.min(),values.max()
        pad=max((hi-lo)*.12,abs(values.mean())*1e-5,1e-6)
        ax.set(xlim=(cycles[0],max(cycles[-1],cycles[0]+1)),ylim=(lo-pad,hi+pad),
               xlabel='Engine operating cycle (cruise snapshot)',ylabel=f'{symbol} ({unit})')
        ax.set_title(f'Sensor {sensor}: {description}',loc='left',fontsize=11,pad=11)
        ax.ticklabel_format(useOffset=False,style='plain',axis='y')
        ax.grid(alpha=.18)
        raw,=ax.plot([],[],color='#8DABBB',linewidth=1,alpha=.85)
        mean,=ax.plot([],[],color='#145C79',linewidth=2.4)
        dot,=ax.plot([],[],'o',color='#D17730',markersize=4)
        cursor=ax.axvline(cycles[0],color='#D17730',linewidth=.8,alpha=.7)
        value_label=ax.text(.02,.95,'',transform=ax.transAxes,va='top',fontsize=9,
                           bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})
        panels.append((values,smooth,raw,mean,dot,cursor,value_label,symbol,unit))
    for ax in list(axes.flat)[len(args.sensors):]:
        ax.set_visible(False)

    def update(i):
        endpoint='simulated failure' if args.split=='train' and i==len(cycles)-1 else 'observed record'
        counter.set_text(f'Operating cycle {cycles[i]} / {cycles[-1]} ({endpoint})     Ground-truth RUL: {rul[i]} cycles')
        for values,smooth,raw,mean,dot,cursor,label,symbol,unit in panels:
            raw.set_data(cycles[:i+1],values[:i+1])
            mean.set_data(cycles[:i+1],smooth[:i+1])
            dot.set_data([cycles[i]],[values[i]])
            cursor.set_xdata([cycles[i],cycles[i]])
            label.set_text(f'{symbol} = {values[i]:.5g} {unit}')
        return []

    frames=list(range(0,len(cycles),args.step))
    if frames[-1]!=len(cycles)-1:
        frames.append(len(cycles)-1)
    # Hold the final frame briefly to allow discussion of the complete path.
    frames += [len(cycles)-1]*args.fps*2
    animation=FuncAnimation(fig,update,frames=frames,interval=1000/args.fps,blit=False,repeat=False)
    output=args.output or ROOT/'output'/f'{args.subset}_{args.split}_engine_{args.engine:03}.mp4'
    if output.suffix.lower() not in ('.mp4','.gif'):
        parser.error('Output must end in .mp4 or .gif')
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.suffix.lower()=='.mp4':
        if not shutil.which('ffmpeg'):
            try:
                import imageio_ffmpeg
                matplotlib.rcParams['animation.ffmpeg_path']=imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                parser.error('For MP4 install imageio-ffmpeg, or use --output animation.gif')
        writer=FFMpegWriter(fps=args.fps,codec='libx264',bitrate=1800,
                            extra_args=['-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2',
                                        '-pix_fmt','yuv420p','-movflags','+faststart'])
    else:
        writer=PillowWriter(fps=args.fps)
    animation.save(str(output),writer=writer,dpi=110)
    update(len(cycles)-1)
    fig.savefig(output.with_suffix('.png'),dpi=140,facecolor='white')
    plt.close(fig)
    print(f'Saved {output} ({len(frames)/args.fps:.1f}s) and its final-frame PNG')


if __name__=='__main__':
    main()

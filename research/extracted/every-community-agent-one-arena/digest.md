Ninety-five community agents sit in a public dataset with their licenses, their provenance and the date
each one was published, and the ninety-three whose terms allow redistribution carry a base64 payload, so
one CSV reconstructs them offline. That is a library. It is not yet a measurement, and the gap between the two is what this
notebook is about.

Three questions decide whether a set of opponents can tell you anything:

1. **How many distinct opponents does it actually hold?** An agent republished under three names is one
   opponent counted three times, and a panel that does not know this reports more evidence than it has.
2. **Which seat did you play?** The market settles slot by slot with player 0 first, so two identical
   agents quoting the same sale on the same turn are not equal. A one-seat table is half a measurement.
3. **How often would you meet each one?** A ladder does not pay for beating the strongest agents
   available. It pays for beating whoever it matches you against.

`arena.py` in the dataset answers all three: the complete matrix over every shop world and both seats,
your own agent as a challenger, and a population weight applied at the end.

**Everything that runs on this page is a SAMPLE, deliberately.** A few hundred games, seconds of compute,
enough to show the shape of the output and to check that the harness is wired correctly. It is not a
measurement.

The real runs belong on your own machine. The complete matrix over this field is 1,830 pairs by 64
worlds by two seats, 234,240 games, which is many hours even on the fast engine; the run whose output
ships with this dataset is 15,872 of them and took an hour and fifty minutes on seven cores. Rebuilding
any of it inside a notebook build would spend shared compute on an answer that is already in the
`examples/` folder, and would time out long before finishing.

Where both exist the page shows them side by side: the sampled run computed live, and the same cut taken
from the finished 15,872-game run. The sample is what you can compute while reading. The full run is what
it would have told you if you had trusted it, and the two disagree often enough to be worth printing
together.

## The engine

The reference environment plays a game in about 241 milliseconds. A bit-exact C++ rewrite plays it in
about 50 microseconds, which is the difference between a complete matrix and a sampled one: 15,872
games is four minutes in one and eleven hours in the other. It ships as source under Apache-2.0, and
`arena.py` falls back to the reference environment automatically when it is absent, so nothing here
depends on the build succeeding.

A notebook runs with no network, so the build cannot reach PyPI for its build dependency and the cell
below compiles the extension directly instead of calling `pip install`. It takes about twenty seconds on a Kaggle worker.
The dataset ships the headers it needs (pybind11 3.1.0, BSD-3-Clause, unmodified, credited in the
dataset README) because the image carries no copy of its own.

[code cell 2: 110 lines]
```
import subprocess, sys, shutil, os, json, tarfile, tempfile, time, pathlib

# FIND the dataset instead of assuming where it is mounted. On this image /kaggle/input
# is not a flat directory of datasets: it holds competitions/ and datasets/<owner>/<slug>/,
# so the files sit three levels down and a hard-coded path misses them.
IN = pathlib.Path('/kaggle/input')
found = None
for root in (IN, pathlib.Path('.')):
    if root.exists():
        found = next(iter(sorted(root.rglob('donors.csv'))), None)
    if found:
        break
if found is None:
    raise SystemExit('attach destbreso/kaggriculture-donor-agents-20260902')
DATA = found.parent
WORK = pathlib.Path('/kaggle/working' if pathlib.Path('/kaggle/working').exists() else 'work')
WORK.mkdir(exist_ok=True)
BUILD = pathlib.Path(tempfile.mkdtemp(prefix='kagsim_'))   # not under WORK: a notebook
# saves everything in its working directory as output, and a compiler leaves a lot there


def unpack(src, into):
    """Kaggle extracts archives on upload, so what was pushed as a tarball arrives as a
    directory carrying its own top-level folder. Take either form, and return a WRITABLE
    copy, because the dataset mount is read only and a compiler writes beside its sources."""
    if src.is_dir():
        dst = into / src.name
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
        return dst
    with tarfile.open(src) as t:
        t.extractall(into)
        top = sorted({m.name.split('/')[0] for m i
```

## Distinct behaviours in the field

The `behaviour_family` column is a measurement, not a guess about whose code resembles whose: two
agents share a family when their full final-bank vector over a reference arena is identical.

[code cell 4: 9 lines]
```
import collections
rows = list(csv.DictReader(open(DATA / 'donors.csv', newline='')))
fam = collections.Counter(r['behaviour_family'] or r['donor_id'] for r in rows)
dupes = {k: v for k, v in fam.items() if v > 1}
print(f'{len(rows)} files, {len(fam)} distinct measured behaviours, '
      f'{sum(v - 1 for v in dupes.values())} of those files are a repeat of another')
for f, n in sorted(dupes.items(), key=lambda kv: -kv[1]):
    members = [r['donor_id'] for r in rows if (r['behaviour_family'] or r['donor_id']) == f]
    print(f'  {n}x identical conduct: ' + ', '.join(sorted(members)))
```

## Agent loading and the entry-point rule

The Kaggle runner takes the **last module-level callable**, not the one named `agent`. Several agents
here are a chassis wrapped by layer after layer, each wrap popping the previous `agent` out of the
namespace. In a few of them the name `agent` survives pointing at an early layer, kept only so the file
can attach telemetry to it. Load that symbol and the agent still runs, still returns legal actions, and
plays a weaker game than its author wrote, silently.

[code cell 6: 32 lines]
```
import importlib.util, base64, tempfile
def last_callable(m):
    name = None
    for k, v in vars(m).items():
        if callable(v) and not k.startswith('_') and getattr(v, '__module__', None) == m.__name__:
            name = k
    return name
tmp = pathlib.Path(tempfile.mkdtemp()); odd, read, failed = [], 0, []
for r in rows:
    if r['payload_included'] != 'True' or r['payload_format'] != 'py':
        continue                      # packaged agents are loaded from their tar by arena.py
    p = tmp / (r['donor_id'] + '.py'); p.write_bytes(base64.b64decode(r['payload_b64']))
    spec = importlib.util.spec_from_file_location('m' + str(abs(hash(p)) % 9999), str(p))
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception as exc:          # counted and named, never passed over in silence
        failed.append((r['donor_id'], f'{type(exc).__name__}: {exc}'[:70]))
        continue
    read += 1
    s = last_callable(m)
    if s and s != 'agent' and 'agent' in vars(m):
        odd.append((r['donor_id'], s))
print(f'{len(odd)} of the {read} single-file agents that import here would lose layers '
      f'if loaded by the name `agent`:')
for n, s in odd:
    print(f'  {n:<48} runner takes `{s}`')
if failed:
    print(f'\n{len(failed)} did not import at all, which is a property of the file and not '
          f'of the loader:')
    for n, why in failed:
        print(f'  {n:<48} {why}')
```

## What to run, and when

`arena.py` is one script with a few switches, and each switch answers a different question. The two runs
on this page are the first and the last row of this table.

| the question you are asking | the run |
|---|---|
| Is my agent ready to submit? | `--challenger MINE=main.py --vs-only --worlds 64 --procs 8` |
| Which of my two candidates is better? | `--challenger A=a/main.py --challenger B=b/main.py --vs-only --worlds 64` |
| What does the field look like NOW? | `--since 2026-09-13` |
| Did my ranking come from the panel I chose? | `--random 12 --worlds 16`, then again with another seed |
| What kind of opponents are these? | `--probe` |
| I already ran it and want another cut | `--replay run.json --games games.csv --matrix matrix.csv` |
| A quick check that the harness works | `--diverse 12 --worlds 6 --procs 4` |
| Everything against everything | no filters, `--worlds N --procs 8` |

Two of them are worth a sentence each.

**The window.** This field turns over in days, so the agents published this week are a different population
from the agents published since the competition opened, and the recent ones are the ones you are about to
meet. Every row in the dataset carries the date of the notebook version it came from, and `--since` and
`--until` cut on it: `--since` alone runs to today, `--until` alone from the beginning, both an interval,
neither the whole snapshot.

**The random panel.** Ranking candidates against a panel you chose can reproduce the choice rather than
measure the agents, which is the failure this notebook is built around. `--random N` draws the panel
instead and prints the seed so the draw repeats. Two draws that agree are evidence the ordering is not an
artefact of the choosing, and that is a control a fixed panel cannot give you.

## Sampled run and full run

Twelve agents, six worlds, both seats: 792 games, a couple of minutes on four cores. Then the same
quantity read off the finished run in the dataset.

The twelve are chosen with `--diverse`, which takes one per measured behaviour family and rotates across
authors. The alternative `--limit 12` takes the first twelve of an alphabetical list, and on this dataset
those are consecutive versions by one author, an opponent set of near clones. A small run has to buy
variety with the few games it can afford.

The finished run has 62 opponents and the dataset carries 61 agents. The difference is one agent of mine
that is not part of the field, and two of the 61 are metadata-only under their authors' terms, so a
reader reproducing that run plays 59 of the 62 rows. The other three are named in the output and can be
fetched from the `source_url` column.

**Run this one locally, not here.** Six agents and four worlds is 120 games and a few seconds. The
mode you actually want, your own agent against all 62 of them over all 64 worlds and both seats, is
7,936 games and roughly an hour on a laptop with the fast engine. That is a local job. This page therefore samples, and the
dataset carries the finished output of a full run.

[code cell 9: 19 lines]
```
# The output STREAMS, line by line, as the games are played. A run that prints only
# when it finishes looks identical to one that has hung, and this one reports its rate
# and what it has left, so a slower machine is visible rather than a mystery.
cmd = [sys.executable, '-u', str((DATA / 'arena.py').resolve()), '--data', str(DATA.resolve()),
       '--diverse', '12', '--worlds', '6', '--procs', '4',
       # one agent in this field runs a neural policy in pure Python and costs 225
       # SECONDS a game. A panel of twelve that happens to draw it is eight hours.
       '--exclude', 'hesoponyo-pure-rl-agent-bc-ppo',
       '--matrix', str((WORK / 'lite_matrix.csv').resolve()),
       '--games', str((WORK / 'lite_games.csv').resolve())]
env = dict(os.environ)
if ENGINE_SRC:                      # the engine was built here, not installed
    env['PYTHONPATH'] = str(ENGINE_SRC) + os.pathsep + env.get('PYTHONPATH', '')
run = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, bufsize=1, env=env)
for line in run.stdout:
    print(line, end='')
if run.wait():
    raise SystemExit(f'arena.py exited with {run.returncode}: the table above is incomplete')
```

[code cell 10: 8 lines]
```
games = pd.read_csv(DATA / 'examples' / 'full_games_20260919.csv')
print(f'the finished run: {len(games):,} game-sides, {games.opponent.nunique()} opponents, '
      f'{games.seed.nunique()} worlds, seats {sorted(games.seat.unique())}')
summary = (games.assign(win=games.margin > 0)
                .groupby('agent')
                .agg(games=('margin', 'size'), win_rate=('win', 'mean'),
                     median_margin=('margin', 'median'), mean_margin=('margin', 'mean')))
summary.round(3)
```

### Figure 1. Win rate against median margin, one point per opponent

Every point is one opponent. The horizontal axis is how often the challenger beat it; the vertical is
the median margin of those games, on a symmetric log scale because the range runs from a few dollars to
tens of thousands.

The cluster on the right is the ordinary case: beaten most of the time, by thousands. The interesting
region is the bottom left, and the two labelled points are why this figure exists. They sit at similar
win rates and at margins two orders of magnitude apart: one is a coin flip between agents within a
rounding error of each other, the other is a defeat. A table of win rates alone cannot tell them apart.

[code cell 12: 29 lines]
```
per = (games.assign(win=games.margin > 0)
            .groupby(['agent', 'opponent'])
            .agg(win_rate=('win', 'mean'), median=('margin', 'median'), n=('margin', 'size'))
            .reset_index())
fig, ax = plt.subplots(figsize=(7.4, 4.4))
for name, colour, mark in (('CAND', COOL, 'o'), ('INC', WARM, '^')):
    d = per[per.agent == name]
    ax.scatter(d.win_rate, d['median'], s=26, c=colour, marker=mark, alpha=.75,
               edgecolor='none', label=name)
ax.set_yscale('symlog', linthresh=100)
ax.axhline(0, color=INK, lw=.8)
ax.axvline(.5, color=INK, lw=.8, ls=':')
near = per[per['median'].abs() < 60].sort_values('win_rate')
far = per[per['median'] < -1500].sort_values('win_rate')
if len(near):
    ax.annotate(f'{len(near)} pairings inside 60 dollars', (near.win_rate.mean(), 0),
                textcoords='offset points', xytext=(18, 26), fontsize=8, color=COOL,
                arrowprops=dict(arrowstyle='-', color=COOL, lw=.7))
if len(far):
    ax.annotate(f'{len(far)} pairings past 1,500 dollars', (far.win_rate.mean(), far['median'].median()),
                textcoords='offset points', xytext=(26, -8), fontsize=8, color=WARM,
                arrowprops=dict(arrowstyle='-', color=WARM, lw=.7))
ax.set_xlabel('share of games won against that opponent')
ax.set_ylabel('median margin, dollars (symlog)')
ax.set_title('Win rate against median margin, one point per opponent')
ax.legend(frameon=False, loc='lower right')
fig.tight_layout(); plt.show()
print('pairings 
```

### Figure 2. Win rate by opponent and world

The arena plays 64 distinct first-two-shop worlds because the shop draw decides which products have
demand, and an agent tuned for one draw is a different agent in another.

Most opponents are a clean sweep in every world and carry no information, so the figure keeps the ones
whose result depends on the world. Rows are worlds, columns are those opponents, and the printed table
below gives the swing between each one's best and worst world. A column with a wide swing is an opponent
whose verdict a four-world sample would decide by luck.

The six are six distinct measured behaviours, not six independent designs: two of them are consecutive
versions by one author, and they are the pair that resists in most worlds. A panel that reports six
columns here is reporting fewer than six opinions.

[code cell 14: 23 lines]
```
cand = games[games.agent == 'CAND'].copy()
cand['win'] = cand.margin > 0
grid = cand.pivot_table(index='world', columns='opponent', values='win', aggfunc='mean')
# Almost every column is a clean sweep, so a 0-to-1 scale over all 62 shows one shade.
# Keep the opponents that vary at all: those are where a world changes the answer.
varying = grid.columns[(grid.min() < 1.0)]
grid = grid[sorted(varying, key=lambda c: grid[c].mean())]
fig, ax = plt.subplots(figsize=(8.4, 6.4))
im = ax.imshow(grid.values, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
ax.set_xticks(range(grid.shape[1]))
ax.set_xticklabels([c[:26] for c in grid.columns], rotation=45, ha='right', fontsize=7)
ax.set_yticks(range(0, len(grid), 2))
ax.set_yticklabels([w[:30] for w in grid.index[::2]], fontsize=6)
ax.set_title(f'Win rate by world for the {grid.shape[1]} opponents that are not a clean sweep\n'
             f'(the other {len(varying.symmetric_difference(cand.opponent.unique()))} are won in every world)',
             fontsize=10)
ax.grid(False)
fig.colorbar(im, ax=ax, shrink=.6, label='share of games won in that world')
fig.tight_layout(); plt.show()
spread = (grid.max() - grid.min()).sort_values(ascending=False)
print('largest swing across worlds, per opponent:')
for k, v in spread.head(5).items():
    print(f'   {k:<46}{v:.0%} between its best and worst world')
```

### Figure 3. The complete matrix of the sample

Everything against everything is what the arena computes, and the sampled run is small enough to show
it whole: twelve agents, 132 ordered pairs, six worlds and both seats behind every cell. The number in
a cell is how often the row agent beat the column agent.

A complete matrix is not a longer ranking table. A ranking says an agent won 60 percent; the matrix says
which opponents those wins came from, and that is where a panel turns out to be narrower than it looks.

[code cell 16: 24 lines]
```
lite = pd.read_csv(WORK / 'lite_matrix.csv')
pair = lite.groupby(['agent', 'opponent'])[['games', 'wins']].sum()
pair['rate'] = pair.wins / pair.games
M = pair['rate'].unstack()
order = M.mean(axis=1).sort_values(ascending=False).index
M = M.loc[order, order]
short = lambda n: n if len(n) <= 26 else n[:25] + '\u2026'

size = max(6.6, 0.62 * len(M))
fig, ax = plt.subplots(figsize=(size, size * .84))
im = ax.imshow(M.values, cmap='RdYlGn', vmin=0, vmax=1)
for i in range(len(M)):
    for j in range(len(M)):
        v = M.values[i, j]
        if v == v:
            ax.text(j, i, f'{v:.0%}', ha='center', va='center', fontsize=7 if len(M) > 8 else 8,
                    color=INK if .25 < v < .75 else 'white')
ax.set_xticks(range(len(M)), [short(n) for n in M.columns], rotation=35, ha='right', fontsize=7)
ax.set_yticks(range(len(M)), [short(n) for n in M.index], fontsize=7)
per_cell = int(lite.groupby(['agent', 'opponent']).games.sum().median())
ax.set_title(f'Sampled run: share of games the row agent won, {per_cell} games a cell')
ax.grid(False)
fig.colorbar(im, ax=ax, fraction=.035, pad=.02).set_label('win rate', fontsize=8)
fig.tight_layout(); plt.show()
```

### Figure 4. The same matrix at full size, 62 opponents by 64 worlds

The finished run is the challenger against every agent in the field, in every world, from both seats:
3,968 cells a side, each one a pair of games that differ only in who sits first.

Each cell is coloured by how many of the two seats the challenger won, so the picture separates a clean
sweep from a split and from a loss. Rows are ordered by how much money the opponent banks in these
games, weakest at the bottom, and the dotted lines mark the quarters used in the next section.

The two panels are the same field seen by two different agents, so the difference between the panels is
the difference between the agents. The names on the right are the rows the incumbent does not sweep, and
the number beside each is how many of that row's 128 seats it lost. The resistance is not spread over the
field: two rows carry most of it, and they are consecutive versions of one author's agent.

[code cell 18: 54 lines]
```
from matplotlib.colors import ListedColormap, BoundaryNorm, SymLogNorm

games['win'] = games.margin > 0
strength = games.groupby('opponent').opponent_bank.median().sort_values(ascending=False)
bands = pd.qcut(strength, 4, labels=['bottom quarter', 'lower middle',
                                     'upper middle', 'top quarter'])
rows = list(strength.index)                          # strongest opponent at the top
hardest = (games[games.agent == 'CAND'].pivot_table(index='world', values='win', aggfunc='mean')
           .sort_values('win').index)                # hardest world on the left
ORDER = ['top quarter', 'upper middle', 'lower middle', 'bottom quarter']

cmap = ListedColormap(['#7f1d1d', '#f59e0b', '#dfe7e1'])
norm = BoundaryNorm([-.5, .5, 1.5, 2.5], cmap.N)
grids = {}
fig, axes = plt.subplots(1, 2, figsize=(11.6, 6.2), sharey=True)
for ax, name in zip(axes, ('CAND', 'INC')):
    d = games[games.agent == name]
    W = d.pivot_table(index='opponent', columns='world', values='win',
                      aggfunc='sum').reindex(index=rows, columns=hardest)
    grids[name] = W
    ax.imshow(W.values, cmap=cmap, norm=norm, aspect='auto', interpolation='nearest')
    lost = int((W.values == 0).sum()); split = int((W.values == 1).sum())
    ax.set_title(f'{name}: {lost} cells lost, {split} split, {W.size - lost - split} swept',
                 fontsize=9)
    ax.set_xlabel('64 shop worlds, hardest on the left')
    ax.set_xticks([]); ax.grid(False)
    for edge in np.flatnon
```

## Bands of opponent strength

A panel is not uniform, and a single win rate over it hides which part of it did the work. The band here
is measured inside the run and not read off a leaderboard: an opponent's strength is the median bank it
takes home across its own 256 games, and the field is cut into quarters by that. The dataset carries no
rating column on purpose, because a rank stored on a file is a timestamp rather than a property and this
field's ladder positions were already stale days after they were captured.

The cut changes what the panel is for:

| band | opponents | CAND win rate | INC win rate | CAND median margin |
|---|---|---|---|---|
| top quarter | 16 | **92.1 %** | **85.0 %** | \$4,128 |
| upper middle | 15 | 99.8 % | 99.2 % | \$8,285 |
| lower middle | 14 | 99.7 % | 99.6 % | \$19,722 |
| bottom quarter | 17 | 100.0 % | 100.0 % | \$47,365 |

Over the whole field the two challengers are 2.0 points apart. **147 of those 160 flipped games, 92
percent of the separation, come from the top quarter alone, which is 26 percent of the run.** The other
three quarters return the same verdict for both agents at a cost of three quarters of the compute.

That is an argument for weighting rather than for dropping the easy bands, and the next section is the
mechanism. Dropped, they stop being available as the control that says an agent has not broken against
ordinary opposition, and an agent that starts losing to the bottom quarter has a defect a top-quarter
score will not show.

[code cell 20: 23 lines]
```
band_of = bands.to_dict()
games['band'] = games.opponent.map(band_of)
ORDER = ['top quarter', 'upper middle', 'lower middle', 'bottom quarter']
full_band = (games.groupby(['band', 'agent'], observed=True)
                  .agg(opponents=('opponent', 'nunique'), games=('margin', 'size'),
                       win_rate=('win', 'mean'), median_margin=('margin', 'median'))
                  .reset_index().pivot(index='band', columns='agent').reindex(ORDER))
print('THE FULL RUN, 15,872 games\n')
print(full_band.round(3).to_string())

lite_games = pd.read_csv(WORK / 'lite_games.csv')
lite_games['win'] = lite_games.margin > 0
lstr = lite_games.groupby('opponent').opponent_bank.median().sort_values()
lbands = pd.qcut(lstr, 4, labels=ORDER[::-1])
lite_games['band'] = lite_games.opponent.map(lbands.to_dict())
lite_band = (lite_games.groupby('band', observed=True)
                       .agg(opponents=('opponent', 'nunique'), games=('margin', 'size'),
                            win_rate=('win', 'mean'), median_margin=('margin', 'median'))
                       .reindex(ORDER))
print('\n\nTHE SAMPLED RUN, the same cut, 240 game sides\n')
print(lite_band.round(3).to_string())
print('\nEach band of the sample holds one or two agents, so the column is a label and not a'
      '\nmeasurement: at this size the quartiles are four names, not four populations.')
```

### Figure 5. Median margin by band and world

The band says which opponents, the world says which shop draw, and the money lives in the interaction.
Both panels share one symmetric log scale, so a cell is comparable across bands and across agents.

The top row is the one to read. Against the top quarter the margin falls to a few thousand dollars, and
for the incumbent it crosses zero in one world, the same world that shows as a column of split cells in
the figure above. Those are the cells where a ranking is decided. The bottom row stays tens of thousands
of dollars from zero in every world, which is what a band that cannot separate two agents looks like.

The annotated cell in each panel is that agent's worst world, and the two are the same pair of shops in
opposite order. The order is part of the world, not a detail of how it is written down: it decides which
shop opens first and therefore which product has demand while the first crops are still growing.

[code cell 22: 25 lines]
```
lim = 64000
fig, axes = plt.subplots(2, 1, figsize=(11.2, 4.8), sharex=True)
for ax, name in zip(axes, ('CAND', 'INC')):
    d = games[games.agent == name]
    G = d.pivot_table(index='band', columns='world', values='margin', aggfunc='median',
                      observed=True).reindex(index=ORDER, columns=hardest)
    im = ax.imshow(G.values, cmap='RdYlGn', aspect='auto', interpolation='nearest',
                   norm=SymLogNorm(linthresh=2000, vmin=-lim, vmax=lim))
    ax.set_yticks(range(len(ORDER)), ORDER, fontsize=8)
    ax.set_title(f'{name}: median margin in dollars, 28 to 34 games a cell',
                 fontsize=9, loc='left')
    ax.set_xticks([]); ax.grid(False)
    worst = np.unravel_index(np.argmin(G.values), G.shape)
    ax.annotate(f'{G.values[worst]:,.0f} in {G.columns[worst[1]]}',
                xy=(worst[1], worst[0]), xytext=(worst[1] + 3, worst[0] + .85),
                fontsize=7, color=INK,
                arrowprops=dict(arrowstyle='-', lw=.6, color=INK))
axes[1].set_xlabel('64 shop worlds, hardest on the left, in the order of the figure above')
cb = fig.colorbar(im, ax=axes, fraction=.02, pad=.01)
cb.set_label('median margin, dollars (symmetric log)', fontsize=8)
plt.show()
floor = (games.groupby(['agent', 'band', 'world'], observed=True).margin.median()
              .groupby(['agent', 'band'], observed=True).min().unstack(0).reindex(ORDER))
print('the worst world of each band, in median margin:')
print(floor.round(0).to_string())
```

## The field against itself

Everything above measures two challengers against the field. This section is the other run: **every agent
published in the last five days against every other**, both seats, with nothing of mine in it. Forty
agents, 780 pairs, 43 shop worlds, **67,080 games**.

The window is the point. A field that turns over in days is a different population every week, and the
agents published this week are the ones a submission today will meet. `--since` cuts the snapshot on the
`published` column, which is why that column exists.

It answers what a per-opponent table cannot. A panel is not a list of names, it is a structure: who beats
whom, how many of these files are really the same opponent, and whether the result is a ladder or a
circle.

**One number from this run is worth carrying into how you read the rest of the page.** The same matrix
over the first FOUR worlds put a different agent first, and the one it crowned is second over 43. Four
worlds separate the far apart and cannot order the close, which is Figure 10 measured on the very run
that produced this table.

[code cell 24: 12 lines]
```
FIELD_GAMES = 'window_games_20260921.csv'
FIELD = DATA / 'examples' / FIELD_GAMES
fg = pd.read_csv(FIELD)
fg['win'] = fg.margin > 0
rank = (fg.groupby('agent')
          .agg(games=('margin', 'size'), win_rate=('win', 'mean'),
               median_margin=('margin', 'median'), median_bank=('bank', 'median'))
          .sort_values('win_rate', ascending=False))
print(f'{fg.agent.nunique()} agents, {len(fg) // 2:,} games, {fg.world.nunique()} worlds, both seats\n')
print('THE TEN THAT WIN MOST')
print(rank.head(10).to_string(float_format=lambda v: f'{v:,.3f}'))
print('\nTHE FIVE THAT WIN LEAST')
```

### Figure 6. Who beats whom, the whole field

Rows and columns are the same agents in the same order, strongest at the top left. A cell is the share of
games the row agent took from the column agent.

Read the structure rather than the cells. A clean ladder would be green above the diagonal and red below
it, with nothing else. What this field shows instead are BLOCKS: squares of agents that split every game
with each other because they are the same agent under different names, and squares that beat everything
below them while losing to everything above. The blocks are the reason a panel of sixty is not sixty
opponents.

[code cell 26: 12 lines]
```
W = (fg.pivot_table(index='agent', columns='opponent', values='win', aggfunc='mean'))
order = rank.index
W = W.reindex(index=order, columns=order)
fig, ax = plt.subplots(figsize=(9.6, 8.6))
im = ax.imshow(W.values, cmap='RdYlGn', vmin=0, vmax=1, interpolation='nearest')
ax.set_xticks([]); ax.grid(False)
ax.set_yticks(range(len(order)), [n[:34] for n in order], fontsize=5)
ax.set_xlabel(f'{len(order)} agents, the same order left to right')
ax.set_ylabel('strongest at the top')
ax.set_title('Share of games the row agent took from the column agent')
fig.colorbar(im, ax=ax, fraction=.03, pad=.02).set_label('win rate', fontsize=8)
fig.tight_layout(); plt.show()
```

### Figure 7. How many opponents this field really holds

Two agents are the same opponent when they bank the same money in the same games. That is a measurement,
not a judgement about whose code resembles whose, and it is the same rule the `behaviour_family` column in
the dataset is built on.

The bar chart is the census: how many files sit in each equivalence class. A class of one is an opponent.
A class of six is one opponent counted six times, and a panel that does not know this reports six times the
evidence it has.

[code cell 28: 22 lines]
```
ref = list(rank.index[len(rank) // 3: len(rank) // 3 + 12])   # a fixed reference panel
key = (fg[fg.opponent.isin(ref)]
       .pivot_table(index='agent', columns=['opponent', 'seed', 'seat'], values='bank'))
# an agent has no games against itself, so its own columns are empty. Fill before the
# join: a missing value is a float and str.join refuses one, which is the whole bug.
sig = key.round(0).fillna(-1).astype('int64').astype(str).agg('|'.join, axis=1)
fam = collections.Counter(sig)
sizes = collections.Counter(fam.values())
dup = sorted([sorted(sig[sig == s].index) for s, n in fam.items() if n > 1], key=len, reverse=True)
print(f'{len(rank)} files, {len(fam)} distinct behaviours measured against a fixed panel of '
      f'{len(ref)} opponents\n')
for group in dup:
    print(f'  {len(group)} files, one behaviour: ' + ', '.join(g[:30] for g in group))

fig, ax = plt.subplots(figsize=(6.8, 3.2))
ks = sorted(sizes)
ax.bar([str(k) for k in ks], [sizes[k] for k in ks], color=COOL, width=.6)
for k in ks:
    ax.text(str(k), sizes[k], f' {sizes[k]}', ha='center', va='bottom', fontsize=8, color=INK)
ax.set_xlabel('files that behave identically'); ax.set_ylabel('classes')
ax.set_title('The field is fewer opponents than it is files')
fig.tight_layout(); plt.show()
```

### Figure 8. Is it a ladder or a circle?

If strength were one number, the matrix would be a total order: sort by win rate and every agent would beat
everyone below it. The upsets are where that fails, and they are what a single-number rating cannot carry.

Each point is a pairing plotted against the gap in overall win rate between the two agents. Points below the
line are upsets: the agent with the worse record over the field wins the direct match. A field with many of
them is a rock-paper-scissors field, and on one of those the ladder position you get depends on who you are
matched against rather than on how good you are.

[code cell 30: 19 lines]
```
pairs = (fg.groupby(['agent', 'opponent']).win.mean().rename('direct').reset_index())
pairs['gap'] = pairs.agent.map(rank.win_rate) - pairs.opponent.map(rank.win_rate)
pairs = pairs[pairs.gap > 0]                       # one row per unordered pair
ups = pairs[pairs.direct < .5]
fig, ax = plt.subplots(figsize=(7.4, 4.2))
ax.scatter(pairs.gap, pairs.direct, s=8, c=COOL, alpha=.35, edgecolor='none', label='pairing')
ax.scatter(ups.gap, ups.direct, s=16, c=WARM, edgecolor='none', label='upset')
ax.axhline(.5, color=INK, lw=.8, ls=':')
ax.set_xlabel('gap in win rate over the whole field')
ax.set_ylabel('share of the direct games the stronger agent took')
ax.set_title('Upsets against the strength gap')
ax.legend(frameon=False, loc='lower right')
fig.tight_layout(); plt.show()
print(f'{len(ups):,} upsets in {len(pairs):,} pairings, {len(ups) / len(pairs):.1%}')
big = ups.sort_values('gap', ascending=False).head(6)
print('\nthe upsets across the widest strength gap:')
for _, r in big.iterrows():
    print(f'  {r.opponent[:34]:36} beats {r.agent[:34]:36} '
          f'{1 - r.direct:.0%} of the time, {r.gap:.0%} below it overall')
```

## What a game actually costs

The engine is not the cost and neither is the harness around it. Measured on this machine, one season:

| what runs | per game |
|---|---|
| the engine alone, both sides passing | **0.73 ms** |
| plus the two observations the harness builds every turn | 32.2 ms |
| plus one agent thinking on one side | 200 to 1,800 ms |

A pairing of two large agents is about 1,600 ms of Python and **0.7 ms of simulator**, so a C++ pass over
the engine would buy two percent of a matrix. The cost is the agents, by construction: these are 300 to
900 kilobyte policies deciding 719 times a game, twice.

That is also the answer to the obvious idea. An agent that ignores its opponent is a recording, and a
recording replays at the engine's speed rather than the policy's. Probed against two very different
rivals over three worlds and both seats, **3 of 83 agents played an identical stream and 80 did not**.
This field reacts, which is what makes it worth playing and what makes it expensive.

### Figure 9. Win rate by seat

Each point is one opponent: the win rate with the challenger in seat 0 against the same with it in
seat 1. A point on the diagonal means the seat made no difference.

Across this field it mostly did not: the median gap between seats is 0.0 percent, 98 of the 124 pairings show
none at all, and the largest is 4.7 percent. That is worth stating because the engine gives seat 0 a real advantage, settling the market
slot by slot with player 0 first, so on any turn where both players quote the same product the seat
decides who sells into the better price.

The reconciliation is in which points leave the diagonal. They are the close pairings, the ones near a
coin flip in Figure 1. Settlement priority decides a game that was otherwise level and is invisible in a
game decided by thousands. So a one-seat table is safe when you are winning comfortably and biased
exactly where the measurement is hardest, which is why the arena plays both by default.

[code cell 33: 16 lines]
```
seat = (games.assign(win=games.margin > 0)
             .pivot_table(index=['agent', 'opponent'], columns='seat', values='win', aggfunc='mean')
             .reset_index())
seat.columns = ['agent', 'opponent', 's0', 's1']
fig, ax = plt.subplots(figsize=(5.4, 5.2))
for name, colour, mark in (('CAND', COOL, 'o'), ('INC', WARM, '^')):
    d = seat[seat.agent == name]
    ax.scatter(d.s0, d.s1, s=28, c=colour, marker=mark, alpha=.7, edgecolor='none', label=name)
ax.plot([0, 1], [0, 1], color=INK, lw=.9, ls='--')
ax.set_xlabel('win rate in seat 0'); ax.set_ylabel('win rate in seat 1')
ax.set_title('Win rate in seat 0 against seat 1, one point per opponent')
ax.legend(frameon=False, loc='lower right')
gap = (seat.s1 - seat.s0).abs()
ax.text(.03, .92, f'median seat gap {gap.median():.1%}\nlargest {gap.max():.0%}',
        transform=ax.transAxes, fontsize=8, color=INK)
fig.tight_layout(); plt.show()
```

### Figure 10. Sampling error of a four-world panel

The lite run uses four worlds because it has to fit in a page view. This figure prices that choice with
the finished data: for each of two thousand random four-world draws, the win rate those four worlds
would have reported against the same opponent set, beside the true value over all 64.

The spread is the sampling error you inherit by ranking on a small panel: a four-world draw can report
either of two agents ahead of the other when the gap between them is smaller than the width shown here.
That is why the arena defaults to the full world list, and why I read a four-world run as a check that
the harness works rather than as a ranking.

[code cell 35: 25 lines]
```
rng = np.random.default_rng(7)
truth = {}
draws = {}
for name in ('CAND', 'INC'):
    d = games[games.agent == name]
    truth[name] = (d.margin > 0).mean()
    seeds = d.seed.unique()
    got = []
    for _ in range(2000):
        pick = rng.choice(seeds, size=4, replace=False)
        got.append((d[d.seed.isin(pick)].margin > 0).mean())
    draws[name] = np.array(got)
fig, ax = plt.subplots(figsize=(7.2, 3.6))
for name, colour in (('CAND', COOL), ('INC', WARM)):
    ax.hist(draws[name], bins=40, alpha=.55, color=colour, label=f'{name}, four worlds')
    ax.axvline(truth[name], color=colour, lw=1.6)
ax.set_xlabel('win rate a four-world sample would have reported')
ax.set_ylabel('draws out of 2,000')
ax.set_title('Vertical lines are the true value over all 64 worlds')
ax.legend(frameon=False)
fig.tight_layout(); plt.show()
for name in ('CAND', 'INC'):
    lo, hi = np.percentile(draws[name], [2.5, 97.5])
    print(f'{name}: true {truth[name]:.1%}, four-world 95% range {lo:.1%} to {hi:.1%} '
          f'(width {hi-lo:.1%})')
```

## Population weighting

Ranking candidates against a panel of the strongest public agents is not the same as ranking them against
the field. Measured once on four of my own agents: an ordering taken against a five-donor panel of strong
notebooks **inverted** when re-scored against recorded ladder opponents, and the ladder agreed with the
recorded opponents. The panel was sound as an instrument and wrong as a population.

`--weights` takes a JSON of agent id to how often you meet it, on any positive scale. Below, three
weightings of the same 15,872 games: every opponent equal, one vote per measured behaviour so a
republished agent counts once, and a skew toward the opponents these two challengers beat most easily,
a crude stand-in for a field of ordinary submissions.

**Figure 11** plots the three, with the table under it. The level moves and the order does not, which is
the outcome you want and cannot assume.

[code cell 37: 24 lines]
```
w = json.loads((DATA / 'examples' / 'weights_one_per_behaviour.json').read_text())
ease = per.groupby('opponent').win_rate.mean()
schemes = {'every opponent equal': lambda o: 1.0,
           'one vote per behaviour': lambda o: w.get(o, 1.0),
           'skewed to the easy half': lambda o: 1.0 / (2.0 - ease.get(o, 1.0))}
tab = []
for label, fn in schemes.items():
    row = {'weighting': label}
    for ag, d in per.groupby('agent'):
        num = sum(fn(o) * r for o, r in zip(d.opponent, d.win_rate))
        row[ag] = round(num / sum(fn(o) for o in d.opponent), 4)
    row['gap'] = round(row['CAND'] - row['INC'], 4)
    tab.append(row)
weighted = pd.DataFrame(tab).set_index('weighting')
fig, ax = plt.subplots(figsize=(6.6, 3.0))
x = np.arange(len(weighted))
ax.bar(x - .18, weighted.CAND, .34, color=COOL, label='CAND')
ax.bar(x + .18, weighted.INC, .34, color=WARM, label='INC')
ax.set_xticks(x); ax.set_xticklabels(weighted.index, fontsize=8)
ax.set_ylim(.9, 1.0); ax.set_ylabel('weighted win rate')
ax.set_title('Weighted win rate under three populations', loc='right', fontsize=9)
ax.legend(frameon=False, loc='lower left', bbox_to_anchor=(0, 1.0), ncol=2, fontsize=8)
fig.tight_layout(); plt.show()
weighted
```

## Engine telemetry

A margin tells you that something changed. It does not tell you whether the thing you built ever fired,
and those are different questions with the same answer shape. A feature that never fired, a feature that
fired two hundred times into a shed that was already full, and a feature that is simply worthless all
read as no effect in the bank.

The engine carries 60 counters for exactly this, maintained on every action and read with
`Game.telemetry(player)`. A few of them, from one real game below:

| counter | what it catches |
|---|---|
| `sell_zero_fill` | market orders that sold nothing and burned one of the ten slots anyway |
| `shed_discarded_units` | production destroyed at the shed cap of 100, which the engine does in silence |
| `hand_pass_turns` | labour bought and not used |
| `fertilizer_forgone` | units offered by the herd and never collected |
| `dead_actions`, `*_dead` | actions the engine accepted and discarded, by verb |
| `silent_loss_coins`, `silent_loss_units` | value lost without any error being raised |

The last row is the point. This environment fails quietly: an order past the tenth slot, a harvest into a
full shed, a FEED with no wheat in hand. None of them raises anything, and all of them are visible here.

[code cell 39: 9 lines]
```
tel = json.loads((DATA / 'examples' / 'telemetry_one_game.json').read_text())
live = {k: v for k, v in sorted(tel.items()) if v}
show = ['sell_zero_fill', 'shed_discarded_units', 'hand_pass_turns', 'farmer_pass_turns',
        'fertilizer_forgone', 'dead_actions', 'silent_loss_units', 'silent_loss_coins',
        'sold_units', 'sell_revenue', 'plant_unwatered_days', 'idle_tile_days']
print(f'{len(tel)} counters, {len(live)} non-zero in this game. The ones worth a look first:')
for k in show:
    if k in tel:
        print(f'   {k:<26}{tel[k]:>12,.0f}')
```

### Cost of reading telemetry

The counters are maintained whether or not you look, so the cost is in the reading and it depends
entirely on how often you read. Two idle agents on this machine, so the engine and not Python is what is
being timed:

| how you read it | per game | against the baseline |
|---|---|---|
| never | 0.61 ms | |
| once at the end of the game | 0.64 ms | **5 % slower** |
| after every one of the 719 steps | 3.22 ms | **5.3 times slower** |

So take it once per game and it is free in practice. Take it every step, which is tempting when you want
a time series, and you have given away most of what the C++ engine bought you. The middle path that works:
read once a day of game time, 30 reads instead of 719.

The cell below re-measures all three on whatever machine is running this page, best of three passes.
The gap between never and once a game is small enough that a shared worker can reverse it; the gap
between never and every step is not.

[code cell 41: 28 lines]
```
try:
    import kagsim, time
    P = {'farmer': ['PASS'], 'hands': [], 'market': []}

    def bench(mode, n, reps=3):
        # best of three: a shared worker's noise is one-sided, so the minimum is the
        # honest estimate of the cost and the mean is an estimate of the neighbours
        best = float('inf')
        for _ in range(reps):
            t0 = time.perf_counter()
            for s in range(n):
                g = kagsim.Game(s)
                while not g.done:
                    g.step(P, P)
                    if mode == 'step':
                        dict(g.telemetry(0))
                if mode == 'game':
                    dict(g.telemetry(0)); dict(g.telemetry(1))
            best = min(best, (time.perf_counter() - t0) / n * 1e3)
        return best

    base, once, every = bench('never', 60), bench('game', 60), bench('step', 8)
    print(f'never read          {base:5.2f} ms a game')
    print(f'once per game       {once:5.2f} ms a game   ({once / base:.2f}x)')
    print(f'after every step    {every:5.2f} ms a game   ({every / base:.2f}x)')
except ImportError:
    print('the C++ engine is not installed here, so this benchmark is skipped;',
          'the table above was measured at 0.61, 0.64 and 3.22 ms a game')
```

## Position of these agents on the ladder

A public notebook agent is not a random opponent. It arrives in numbers, it settles in the middle, and
it fades. All three are measurable and I have measured them on my own episodes rather than inferred them.

**They arrive in numbers.** Counted over 141 of my own rated games, 120 of the opponents, 85 percent,
were running the same published base I was. One family inside that went from 3.1 percent of the field on
one day to 9.1 percent on the next and 47.5 percent on the third: a factor of fifteen in three days. A
strong notebook does not add an opponent to the ladder, it repaints a large share of it.

**They settle in the middle.** Over the eighteen highest-rated submissions on the same day, sixteen open
by buying an animal and **none** carries the opening signature of that dominant published family. So the
family that is 85 percent of the opponents in my band is close to zero percent of the top. These agents
reach a respectable rating and stop there. They are therefore a good measuring stick and a poor model of
the leaders.

**They fade.** The field as a whole turns over with a half life measured at **2.1 days**. A panel built
from today's notebooks describes a population that is half gone within a week. The dataset is therefore
dated in its subtitle and every row carries a sha256, so that a result taken against these agents stays
interpretable after the agents themselves are gone.

None of this makes the field less useful. It makes it useful for a specific thing: a hard, varied,
reproducible test of any agent you are about to field, and a stable substrate for studies that need many
strong opponents whose code you can read. It makes it useless as a forecast of a rating.

### Scope of the weighting

`--weights` exists because of the gap between those two uses. If you can estimate how often you would
actually meet each agent, weighting the per-opponent win rates by that frequency moves the number toward
what a ladder in your band would pay you, and away from what a panel of equals would. The right weight
is not one per file: it is one per **cluster**, scaled by how large that cluster is on the ladder right
now. An agent republished under three names is one cluster of size three by file count and possibly a
quarter of a rating band by seat count, and those are different numbers.

The shipped example does the cheap half of this, one vote per measured behaviour, which at least stops a
republished agent from voting three times. The expensive half, estimating each cluster's true size in a
band from live episodes, is a separate piece of work and is **out of scope here**: it needs a sample of
real matchups rather than a corpus of code, and it decays with the same 2.1-day half life as everything
else. What this notebook can say is that the machinery accepts any weighting you can justify, that the
ordering survived all three I tried, and that a disagreement between the raw and weighted columns is
information about the panel rather than about the agents.

## Your agent

If you published an agent for this competition and it is not in the dataset, say so in the comments and
I will add it. All I need is the notebook URL: the file lands there byte-identical, credited to you,
under the license your notebook carries, and it joins the next run of the matrix above.

The same goes for a correction. If a row credits you wrongly, or your notebook has moved on and the copy
here is stale, tell me and I will refresh it. If you would rather not be included at all, say so and the
row goes.

What the snapshot cannot do by itself is keep up: the field publishes faster than any fixed panel can
track, which is the whole argument for dating it and for the half life in the section above.

## Limitations

This field is made of strong public notebook agents. It is a hard-opponent stress test rather than the
population a ladder pairs you with, so an adoption decision taken on it alone is taken on the wrong
population. Two habits make it safe:

* score the same candidates on a second population sharing as little as possible with the first, and read
  whether the ORDER survives rather than whether the numbers agree;
* prefer the weighted column wherever you have any estimate of who you actually meet, and treat a
  disagreement between the two as information about the panel rather than about the agents.

Every agent in the dataset belongs to its author, is credited in the `author` and `source_url` columns,
and ships under the license its notebook states. The two whose notebooks state no redistributable license
are metadata-only, by their authors' terms.
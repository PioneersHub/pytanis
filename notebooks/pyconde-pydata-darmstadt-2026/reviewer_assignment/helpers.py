"""Helper functions for reviewer assignment."""

from __future__ import annotations

import logging
import pickle
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
from matplotlib.axes import Axes

from pytanis.review import Col, save_assignments_as_json


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def load_track_mapping(path: str | Path = 'config/track_mapping.yaml') -> tuple[dict[str, str], dict[str, str]]:
    """Flatten nested track mapping into single dict. loads the mapping of the submissions to reviews. this might have to be updated every year."""
    data = load_yaml(path)
    mapping: dict[str, str] = {}
    for section in ['general', 'pycon', 'pydata']:
        mapping.update(data.get(section, {}))
    return mapping, data.get('preference_aliases', {})


def load_column_mapping(path: str | Path = 'config/column_mapping.yaml') -> dict[str, str]:
    """Google sheet to pretalx mapping"""
    return load_yaml(path)['gsheet_columns']


def setup_plotting() -> None:
    """Setups that we usually have in the top of the notebook. they are better here :)"""
    sns.set_context('poster')
    sns.set(rc={'figure.figsize': (12, 6.0)})
    sns.set_style('whitegrid')
    pd.set_option('display.max_rows', 120)
    pd.set_option('display.max_columns', 120)


def build_reviews_df(revs: list[Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build reviews dataframe and count scored reviews per submission."""
    scored = [r.submission for r in revs if r.score is not None]

    if scored:
        counts = pd.Series(scored).value_counts().reset_index()
        counts.columns = [Col.submission, Col.nreviews]
    else:
        counts = pd.DataFrame({Col.submission: [], Col.nreviews: []})
    df = pd.DataFrame({
        'created': [r.created for r in revs],
        'updated': [r.updated for r in revs],
        Col.pretalx_user: [r.reviewer_name or r.reviewer_code for r in revs],
        'score': [r.score for r in revs],
        'review': [r.submission for r in revs],
    })
    return df, counts


def prepare_submissions(
    subs_as_df_func: Callable[[list[Any]], pd.DataFrame],
    subs: list[Any],
    rev_counts: pd.DataFrame,
    target_reviews: int,
    community_map: tuple[str, str],
    track_mapping: dict[str, str],
) -> pd.DataFrame:
    """Filter and prepare submissions dataframe."""
    df = subs_as_df_func([s for s in subs if s.state.value == 'submitted'])
    df = df.loc[df[Col.pending_state].isnull()]
    df.replace({Col.track: dict([community_map])}, inplace=True)
    df[Col.track] = df[Col.track].map(lambda x: track_mapping.get(x, x))
    df[Col.target_nreviews] = target_reviews
    df = pd.merge(df, rev_counts, on=Col.submission, how='left')
    df[Col.nreviews] = df[Col.nreviews].fillna(0).astype(int)
    df[Col.rem_nreviews] = (df[Col.target_nreviews] - df[Col.nreviews]).clip(lower=0)

    return df


def prepare_reviewers(
    gsheet_df: pd.DataFrame,
    revs_df: pd.DataFrame,
    col_mapping: dict[str, str],
    community_map: tuple[str, str],
    pref_aliases: dict[str, str],
) -> tuple[pd.DataFrame, list[str]]:
    """Prepare reviewers dataframe from Google Sheet data."""
    internal_col_map: dict[str, Any] = {}
    for src, dst in col_mapping.items():
        if hasattr(Col, dst):
            internal_col_map[src] = getattr(Col, dst)
        else:
            internal_col_map[src] = dst
    df = gsheet_df.rename(columns=internal_col_map).copy()
    df[Col.track_prefs] = df[Col.track_prefs].apply(lambda x: x.replace(community_map[0], community_map[1]).split(', '))
    df[Col.track_prefs] = df[Col.track_prefs].apply(lambda prefs: [pref_aliases.get(p, p) for p in prefs])
    df = df.loc[~df[Col.pretalx_activated].isna()]
    assign_all = df[Col.email].loc[df[Col.all_proposals] == 'x'].str.strip().tolist()
    revs_grouped = revs_df.groupby(Col.pretalx_user).agg(list).reset_index()
    df = pd.merge(df, revs_grouped, on=Col.pretalx_user, how='left')
    df['review'] = df['review'].apply(lambda x: x if isinstance(x, list) else [])
    df[Col.curr_assignments] = df['review'].map(list)
    df[Col.done_nreviews] = df['score'].map(
        lambda s: 0 if not isinstance(s, list) else sum(1 for x in s if not np.isnan(x))
    )

    return df, assign_all


def validate_mappings(
    revs_user_df: pd.DataFrame,
    gsheet_df: pd.DataFrame,
    col_mapping: dict[str, str],
) -> None:
    """Ensure all reviewers in pretalx can be mapped to gsheet."""
    pretalx_col = 'Pretalx Name'
    known = set(gsheet_df[pretalx_col])
    found = set(revs_user_df[Col.pretalx_user])
    if unmapped := found - known:
        raise RuntimeError(f'Unmapped review authors: {", ".join(unmapped)}')


def plot_reviews_per_proposal(subs_df: pd.DataFrame) -> Axes:
    """Plots the review per proposal total"""
    data = subs_df[Col.nreviews].value_counts().reset_index()
    data.columns = ['#Reviews', '#Proposal']
    ax = sns.barplot(data, x='#Reviews', y='#Proposal')
    ax.set_title('Number of reviews per proposal')
    ax.set(ylim=(0, len(subs_df)))
    return ax


def plot_progress(subs_df: pd.DataFrame, target_reviews: int) -> Axes:
    """Plots the progress of the review process."""
    progress = subs_df.copy()
    progress[Col.nreviews] = progress[Col.nreviews].clip(upper=target_reviews)
    totals = progress[[Col.target_nreviews, Col.nreviews]].sum()
    _, ax = plt.subplots(figsize=(15, 1))
    sns.set_color_codes('pastel')
    sns.barplot(x=[totals[Col.target_nreviews]], color='b')
    sns.set_color_codes('muted')
    sns.barplot(x=[totals[Col.nreviews]], color='b')
    ax.set_title('Review Progress')
    pct = totals[Col.nreviews] / totals[Col.target_nreviews]
    ax.bar_label(ax.containers[1], labels=[f'{pct:.1%}'])
    return ax


def plot_reviewer_stats(reviewers_df: pd.DataFrame) -> None:
    """Charts the starts of the reviewers"""
    data = reviewers_df[Col.done_nreviews].value_counts().reset_index()
    data.columns = ['Done #Reviews', '#Reviewers']
    ax = sns.barplot(data, y='#Reviewers', x='Done #Reviews')
    ax.set_title('Reviews done per reviewer')
    plt.show()

    top = reviewers_df[[Col.speaker_name, Col.done_nreviews]].sort_values(Col.done_nreviews, ascending=False)
    _, ax = plt.subplots(figsize=(12, 24))
    sns.barplot(top, y=Col.speaker_name, x=Col.done_nreviews)
    ax.set_title('Top reviewers')
    plt.show()

    active = (reviewers_df[Col.done_nreviews] > 0).sum()
    total = len(reviewers_df)
    _, ax = plt.subplots(figsize=(15, 1))
    sns.set_color_codes('pastel')
    sns.barplot(x=[total], color='g')
    sns.set_color_codes('muted')
    sns.barplot(x=[active], color='g')
    ax.set_title('Active Reviewers')
    ax.bar_label(ax.containers[1], labels=[f'{active / total:.1%}'])
    plt.show()

    exploded = reviewers_df[[Col.track_prefs]].explode(Col.track_prefs)
    counts = pd.get_dummies(exploded, prefix='', prefix_sep='').sum()
    ax = sns.barplot(x=counts.index, y=counts.values)
    plt.xticks(rotation=90)
    ax.set_title('Track Preferences')
    ax.set_ylabel('#Reviewers')


def assign_proposals(
    subs_df: pd.DataFrame,
    reviewers_df: pd.DataFrame,
    buffer: int,
) -> pd.DataFrame:
    """
    Assign proposals to reviewers based on track preference and workload.
    Returns updated reviewers_df with assignments.
    """
    COL_REM = 'Remaining Assignments'
    COL_N = 'Current #Assignments'

    subs: pd.DataFrame = pickle.loads(pickle.dumps(subs_df))
    revs: pd.DataFrame = pickle.loads(pickle.dumps(reviewers_df))
    revs[Col.curr_assignments] = revs['review'].map(list)

    reviewer_prefs: set[str] = {p for prefs in revs[Col.track_prefs] for p in prefs}
    sub_tracks: set[str] = set(subs[Col.track].dropna())

    if uncovered := sub_tracks - reviewer_prefs:
        raise RuntimeError(f'No reviewers for tracks: {uncovered}')
    if unused := reviewer_prefs - sub_tracks:
        logging.warning(f'Unused reviewer preferences: {unused}')

    subs = subs.sort_values(Col.rem_nreviews, ascending=False)
    assigned_counts = revs[Col.curr_assignments].explode().value_counts()
    subs[COL_N] = subs[Col.submission].map(assigned_counts).fillna(0)
    subs[COL_REM] = subs[Col.rem_nreviews].where(
        subs[Col.rem_nreviews] == 0,
        subs[Col.rem_nreviews] + buffer - subs[COL_N],
    )
    revs[COL_N] = revs[Col.curr_assignments].apply(len)

    def find_reviewer(sub_code: str, track: str) -> int:
        has_pref = revs[Col.track_prefs].map(lambda x: track in x)
        already = revs[Col.curr_assignments].map(lambda x: sub_code in x)
        candidates = has_pref & ~already

        if not revs.loc[candidates].empty:
            return revs.loc[candidates, COL_N].idxmin()

        logging.warning(f'No preferred reviewer for {sub_code}')
        return revs.loc[~already, COL_N].idxmin()

    while subs[COL_REM].sum() > 0:
        for idx, row in subs.iterrows():
            if row[COL_REM] <= 0:
                continue
            rev_idx = find_reviewer(row[Col.submission], row[Col.track])
            revs.loc[rev_idx, Col.curr_assignments].append(row[Col.submission])
            revs.loc[rev_idx, COL_N] += 1
            subs.loc[idx, COL_REM] -= 1

    return revs


def add_all_proposals_reviewers(
    assign_df: pd.DataFrame,
    reviewers_df: pd.DataFrame,
    emails: list[str],
    all_codes: list[str],
) -> pd.DataFrame:
    """Add reviewers who want all proposals."""
    COL_N = 'Current #Assignments'
    rows: list[dict[str, Any]] = []

    for email in emails:
        mask = reviewers_df[Col.email].fillna('').str.strip() == email
        if mask.any():
            row = reviewers_df.loc[mask].iloc[0].to_dict()
            row[Col.curr_assignments] = all_codes.copy()
            row[COL_N] = len(all_codes)
            rows.append(row)
            logging.info(f'Added {email} with all proposals')
        else:
            logging.warning(f'{email} not found')
    if rows:
        return pd.concat([assign_df, pd.DataFrame(rows)], ignore_index=True)
    return assign_df


def save_assignments(df: pd.DataFrame, output_dir: str | Path = 'output') -> str:
    """save the assignments to json."""
    Path(output_dir).mkdir(exist_ok=True)
    filename = f'{output_dir}/assignments_{date.today():%Y%m%d}.json'  # noqa: DTZ011
    save_assignments_as_json(df, filename)
    return filename

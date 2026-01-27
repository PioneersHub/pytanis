# Reviewer Assignment

## Introduction

Hello dear PC member. So you want to assign reviewers and contribute to the great shuffling experience. Look no further cause this is where it all starts.

## Setup

In order to randomize the world for the submitters and the reviewers, some important conditions have to be fullfilled first:

1. Do you have admin rights for pretalx?: This is a prerequisite. you cannot shuffle if you're not an admin.

2. do you have your credentials in check?: this is also a prerequisite. this link tells you everyhting (https://pioneershub.github.io/pytanis/latest/usage/installation/)

3. Do you know how to use python? joking, we know you do.

4. do you have the environment installed? here is where and how to do it: pytanis/README.md

## Steps

0. Uptade track mapping and make sure the code is not broken.
1. ` hatch run jupyter lab`.
2. Execute every cell or all the cells at once.
3. go to pretalax and upload the json under: review -> assign reviewers -> assign reviewers individually -> action  -> import assignments -> upload -> replace current asignments.
4. Write in the program channel of discord that update is done

## Folder structure

- config/ : contains two files:
  - track_mapping.yaml: this is the submission to reviewing preferences mapping. Might change every year
  - column_mapping.yaml: this is the google sheet column name to column names in the code.

- output/ : this is not pushed but will be created automatically. will contain the assignments
- assign_reviewers.ipynb: the star of the show. the notebook that will give you the power to shuffle
- helpers.py: functions used by assign_reviewers.ipynb notebook.

## What to do if you are blocked

Some advice in case you are lost or need help:
- reach out to Florian Wilhelm, Amine Jebari or Nils Mohr.
- Read src/pytanis/pretalx, this can be very helpful when issues arise.
- check https://github.com/pretalx/pretalx as we are mostly wrapping what they do.

## Contribution

1. do you have contribute rights? Ask Florian.
2. check the README in the root of the repo.
3. Create a branch.

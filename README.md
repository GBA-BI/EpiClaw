# EpiClaw

EpiClaw is a project built on top of [OpenClaw](https://github.com/openclaw/openclaw) for our own domain scenarios.

It is designed to extend OpenClaw with our team-specific Epi skills, while gradually adding the ability to connect with BioOS and operate BioOS resources. The goal is to make EpiClaw a more practical capability layer for epidemic prevention, early warning, and bioinformatics-related workflows.

## What is this repository for

This repository is mainly used for two things:

1. **Collecting and organizing our team-specific skills**
2. **Extending EpiClaw with BioOS-related capabilities**

At this stage, the repository mainly serves as a place to accumulate reusable skills for our internal use cases.

## Current positioning

EpiClaw is currently under development.

Right now, this repository is mainly used to collect skills for our teammates. Everyone can put their own scenario-specific skills into the `skills/` directory, so that these skills can be gradually accumulated, reused, and improved.

Typical examples may include:


- epidemic prevention / early warning related skills
- data analysis related skills
- bioinformatics analysis related skills
- workflow orchestration related skills
- BioOS resource operation skills
- domain-specific helper skills for internal use

## BioOS integration

One important direction of EpiClaw is to connect with **BioOS**, so that the agent can gradually gain the ability to interact with BioOS resources, such as:

- viewing or operating workspace resources
- interacting with workflows
- managing files or analysis outputs
- supporting domain workflows on top of BioOS

This part is still evolving.

## Repository structure

```text
EpiClaw/
├── README.md
└── skills/
```

README.md: project introduction
skills/: place for team-specific skills

## How to contribute

If you want to add a new skill, please put it under the `skills/` directory and organize it with a clear name and structure.

Recommended principles:

- one skill for one clear purpose
- keep naming explicit and understandable
- document inputs, outputs, and usage when necessary
- make it easy for other teammates to reuse

## Vision

We hope EpiClaw can gradually become a practical capability layer built on OpenClaw for our own scenarios:

- continuously accumulating team-specific skills
- continuously enhancing BioOS integration
- eventually forming a more usable agent capability set for our real-world work
name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["bug", "triage"]
assignees:
  - brpaz
body:
  - type: markdown
    attributes:
      value: |
        99% of issues related with an extension not working are related with a missing Python dependency that the extension needs.

        Before open any issue, please make sure to check the project README for a list of Python extensions to install.

        Check this [Page](https://ulauncher-extension-doesnt-install-and-now.netlify.app/) for debugging help.
  - type: textarea
    id: description
    attributes:
      label: Descprition?
      description: Please explain the issue that you found.
    validations:
      required: true
  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      description: |
        Please copy and paste the extension logs. The best way to get them:
        - Close any Ulauncher instance that you have running
        - From the command line run: `ulauncher -v --dev |& grep "extension-name"`
        - Execute the action that is giving error.
      render: shell

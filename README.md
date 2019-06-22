# Ulauncher Github

[![Ulauncher Extension](https://img.shields.io/badge/Ulauncher-Extension-green.svg?style=for-the-badge)](https://ext.ulauncher.io/-/github-brpaz-ulauncher-github)
[![CircleCI](https://img.shields.io/circleci/build/github/brpaz/ulauncher-github.svg?style=for-the-badge)](https://circleci.com/gh/brpaz/ulauncher-github)
![License](https://img.shields.io/github/license/brpaz/ulauncher-github.svg?style=for-the-badge)

> [ulauncher](https://ulauncher.io/) Extension that provides quick access to common [GitHub](https://github.com) functionality like your repositories or gists.

## Usage

![demo](demo.gif)

## Features

- Search public repos
- Search uers
- Quick access to your profile pages, Issues, Pull Requests etc
- List your repos, organizations and gists.

## Requirements

- [ulauncher 5](https://ulauncher.io/)
- Python > 3
- PyGithub Extension (install with `pip install pygithub`)

## Install

Open ulauncher preferences window -> extensions -> add extension and paste the following url:

`https://github.com/brpaz/ulauncher-github`

## Usage

- Before usage you need to configure your Github "access_token" in plugin preferences. You can get one [here](https://github.com/settings/tokens).

### Keywords

Besides the main "gh" keyword, which triggers the main extension workflow, this extension have some other keywords that allows you access some of most used actions quickly.

- gists - Access to your Gists
- ghrepos -> Access to your Repos
- ghsearch -> Do a repository search

## Notes

- Repositories, Stars and Gists are cached for 1 day. You can clear your cache, restarting ulauncher or selecting "Refresh cache" from the extension main menu.

## Development

```
git clone https://github.com/brpaz/ulauncher-github
make link
```

To see your changes, stop ulauncher and run it from the command line with: `ulauncher -v`.

## TODO

- Cache user repositories, gists and organizations in background for faster results.

## Contributing

ALl contributions are welcome.

## Show your support

<a href="https://www.buymeacoffee.com/Z1Bu6asGV" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>


## License 

Copywright @ 2019 [Bruno Paz](https://github.com/brpaz)

This project is [MIT](LLICENSE) Licensed.

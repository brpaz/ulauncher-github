# Ulauncher Github

> [ulauncher](https://ulauncher.io/) Extension for interacting with your [GitHub](https://github.com)

## Usage

![demo](demo.gif)

## Features

* Search public repos
* Search uers
* Quick access to your profile pages, Issues, Pull Requests etc
* List your repos, organizations and gists.

## Requirements

* [ulauncher](https://ulauncher.io/)
* Python >= 2.7
* PyGithub Extension (install with ```pip install pygithub```)

## Install

Open ulauncher preferences window -> extensions -> add extension and paste the following url:

```https://github.com/brpaz/ulauncher-github```

## Usage

* Before usage you need to configure your Github "access_token" in plugin preferences. You can get one [here](https://github.com/settings/tokens).

## Notes

* Some requests are cached for better performance. Starred Repos and Organizations have a cache TTL of 1h and user repositories have a cache TTL of 30m.

## Development

```
git clone https://github.com/brpaz/ulauncher-github
cd ~/.cache/ulauncher_cache/extensions/ulauncher-github
ln -s <repo_location> ulauncher-github
```

To see your changes, stop ulauncher and run it from the command line with: ```ulauncher -v```.


## TODO 

* Cache user repositories, gists and organizations in background for faster results.


## License 

MIT

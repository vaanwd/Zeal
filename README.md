# Zeal for Sublime Text

[Zeal][] integration for Sublime Text.
[Zeal][] is an offline documentation browser which similar to [Dash][].

[Zeal]: https://zealdocs.org/
[Dash]: https://kapeli.com/dash/

Tested on Windows & Linux.


## Usage

- <kbd>F1</kbd> - Search for the currently selected word.
  Shows a selection list if multiple docsets match for the current file.

  ![code](https://user-images.githubusercontent.com/931051/82086247-85d60500-96ee-11ea-83e2-154094db1af4.png)
  ![docset list](https://user-images.githubusercontent.com/931051/82086077-414a6980-96ee-11ea-8fa6-b3d895f97b1f.png)

- <kbd>Shift</kbd>&nbsp;<kbd>F1</kbd> - Custom search in Zeal docsets.

  ![custom search](https://user-images.githubusercontent.com/931051/82086076-40b1d300-96ee-11ea-92ae-9b922bd2434a.png)


## Installation

The easiest way to install the package
is to use [Package Control](https://packagecontrol.io/).
Choose *Package Control: Install Package* in the Command Palette
(<kbd>Ctrl</kbd>&nbsp;<kbd>Shift</kbd>&nbsp;<kbd>P</kbd>)
and select "Zeal" from the list.

### Using Git

Go to your Sublime Text `Packages` directory and clone the repository using the command below:

    $ git clone https://github.com/vaanwd/Zeal "Zeal"

### Download Manually

1. Download the files using the GitHub .zip download option.
1. Unzip the files and rename the folder to `Zeal`.
1. Copy the folder to your Sublime Text `Packages` directory.


## Configuration

Select `Preferences: Zeal Settings` form the command palette
to open the configuration files.

If your zeal executable cannot be found by default,
change the `zeal_command` setting.

To add more docsets to choose from,
add entries to the `docsets_user` list.


[&copy; 2014 Vaan Web Design](https://www.vaanwebdesign.ro) <br>
[&copy; 2020 FichteFoll](https://github.com/FichteFoll)

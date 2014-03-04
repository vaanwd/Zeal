# Zeal for Sublime Text 2/3

Zeal package for Sublime Text using [Zeal](http://zealdocs.org/) documentation browser which is similar with [Dash](http://kapeli.com/dash/).

*Tested in Windows/Linux.*  

##Screen-shots

Multiple results for PHP mapping.

![Multiple results for PHP mapping](http://www.vaanwebdesign.ro/includes/images/zeal_1.png)
<br/>
<br/>
Custom search in Zeal docsets.

![Custom search in Zeal docsets](http://www.vaanwebdesign.ro/includes/images/zeal_2.png)

## Installation

Easiest way to install the plugin is to use [Package Control](http://wbond.net/sublime_packages/package_control).

Alternatively you can clone with git directly into `Packages` directory in the Sublime Text 2 application settings area. The directory name must be `Zeal`.

### Using Git

Go to your Sublime Text 2 `Packages` directory and clone the repository using the command below:

    git clone https://github.com/vaanwd/Zeal "Zeal"

### Download Manually

* Download the files using the GitHub .zip download option
* Unzip the files and rename the folder to `Zeal`
* Copy the folder to your Sublime Text 2 `Packages` directory

## Usage

`F1` - Open Zeal documentation for current/selected word.

`Shift` + `F1` - Open Zeal search bar.

## Mapping example
To mapping other language for Zeal docset you need to edit `User\Zeal.sublime-settings`:

	{
	  /**
	   *  Zeal executable path.
	   *  For Linux: /usr/bin/zeal
	   *  For Windows: c:\\Program Files\\Zeal\\zeal.exe
	   */
	  "zeal_command": "/usr/bin/zeal",

	  /**
	   * Language mapping examples.
	   */
	  "language_mapping": {
	    "HTML": {"lang": "html", "zeal_lang": "html"},
	    "JavaScript": {"lang": "javascript", "zeal_lang": "javascript"},
	    "CSS": {"lang": "css", "zeal_lang": "css"},
	    "CSS MSN": {"lang": "css", "zeal_lang": "msdn"},
	    "PHP": {"lang": "php", "zeal_lang": "php"},
	    "Drupal": {"lang": "php", "zeal_lang": "drupal"},
	    "Python": {"lang": "python", "zeal_lang" : "python"},
	    "Django": {"lang": "python", "zeal_lang" : "django"}
	  }
	}


[&copy; 2014 Vaan Web Design](http://www.vaanwebdesign.ro)


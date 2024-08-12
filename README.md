<img src="https://iili.io/J8wvc1n.png" width="64" height="64" align="right" />

# AskAI
>
> Unleash the Power of AI in Your Terminal

[![Terminal](https://badgen.net/badge/icon/terminal?icon=terminal&label)](https://github.com/yorevs/homesetup)
[![License](https://badgen.net/badge/license/MIT/gray)](LICENSE.md)
[![Release](https://badgen.net/badge/release/v1.0.11/gray)](docs/CHANGELOG.md#unreleased)
[![Donate](https://badgen.net/badge/paypal/donate/yellow)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=J5CDEFLF6M3H4)
[![build-and-test](https://github.com/yorevs/askai/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/yorevs/askai/actions/workflows/build-and-test.yml)

<img src="https://iili.io/J8vkAYX.png" width="100%" height="100%" />

---

<img src="https://iili.io/J8wrBSe.png" width="360" height="360" align="right" />

Born from the idea of empowering individuals with disabilities to navigate the digital world effortlessly, AskAI stands as a beacon of accessibility in the realm of computing. It emerges as a revolutionary solution, harnessing the prowess of AI to bridge the gap between users and the terminal interface. With its intuitive design, AskAI welcomes users of all abilities, eliminating the need for extensive familiarity with shells like bash or zsh. Now, individuals with disabilities can effortlessly command their machines, whether it involves listing files and folders, summarizing documents, accessing real-time data, or delving into a myriad of other functions.

At the heart of AskAI lies its innovative integration of Speech-to-Text and Text-to-Speech technologies, offering a seamless experience for both visually and hearing impaired users. Through these cutting-edge features, individuals can interact with their computers using their natural voice, transcending the barriers imposed by traditional input methods. Moreover, AskAI introduces a unique push-to-talk input mechanism, enabling users to issue commands effortlessly, enhancing the fluidity and ease of interaction.

<img src="https://iili.io/J8wiCqQ.png" style="padding-right: 10px" width="270" height="154" align="left" />

Furthermore, AskAI embraces diversity by breaking language barriers, ensuring that no matter the tongue spoken, users can communicate effectively with their systems. Its adaptive language capabilities ensure that commands are understood and executed accurately, regardless of linguistic nuances. By championing inclusivity on all fronts, AskAI redefines the landscape of computing accessibility, empowering individuals with disabilities to navigate the digital realm with confidence and autonomy.


> The world speaks many languages. AskAI understands them all.

🔥 **HOT** 🔥 Checkout the [YouTube](https://www.youtube.com/watch?v=ZlVOisiUEvs) video with our Demo!

[![YouTube Video](https://img.youtube.com/vi/ZlVOisiUEvs/0.jpg)](https://www.youtube.com/watch?v=ZlVOisiUEvs)


## Key Features

- Seamlessly Integrate AI Models (Currently Supporting OpenAI).
- Activate Speech-to-Text Inputs via Push-to-Talk Keybinding.
- Control Text-to-Speech Outputs with Adjustable Speed.
- Enable Assistive Technology for Visually Impaired Terminal Usage.
- Enjoy a Natural Typewriter Effect Synced with Speaking Text.
- Automate Offline Language Translations for Enhanced Accessibility.
- Interactive and Non-Interactive modes.
- Image captions to provide textual descriptions for visual content.
- Enhanced accuracy in responses is achieved through the implementation of a Retrieval-Augmented Generation (RAG) system.

## Installation

### Requirements

#### Python

- Python 3.10 and higher

#### Operating Systems

- Darwin
  - High Sierra and higher
- Linux
  - Ubuntu 16 and higher
  - CentOS 7 and higher
  - Fedora 31 and higher

You may want to install HsPyLib on other OS's and it will probably work, but there are no guarantees that it
**WILL ACTUALLY WORK**.

#### Applications / Libraries

The following software are required:

- FFMPEG (To allow playing audio and video files from your terminal).
- PORTAUDIO (To allow microphone recordings).

##### macOS installation

Use Homebrew to install the prerequisite portaudio:

```bash
$ brew install portaudio ffmpeg libmagic
```

##### GNU/Linux installation

Debian-based systems:

```bash
$ sudo apt install python3-pyaudio ffmpeg libmagic-dev
```

RedHat-based systems:

```bash
$ sudo dnf install portaudio-devel redhat-rpm-config ffmpeg libmagic-dev
```

#### AskAI installation

AskAI is available at [PyPi](https://pypi.org/project/hspylib-askai/)

```bash
$ python3 -m pip install hspylib-askai
```

## Support

> Your support and contributions are greatly appreciated in helping us improve and enhance HomeSetup. Together, we can
make it even better!

You can support HomeSetup by [donating](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=J5CDEFLF6M3H4)
or contributing code. Feel free to contact me for further details. When making code contributions, please make sure to
review our [guidelines](docs/CONTRIBUTING.md) and adhere to our [code of conduct](docs/CODE_OF_CONDUCT.md).

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/yorevs)

You can also sponsor it by using our [GitHub Sponsors](https://github.com/sponsors/yorevs) page.

This project is already supported by:

<a href="https://www.jetbrains.com/community/opensource/?utm_campaign=opensource&utm_content=approved&utm_medium=email&utm_source=newsletter&utm_term=jblogo#support">
  <img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="120" height="120">
</a>

Thank you <3 !!

## Contacts

- License: [MIT](LICENSE.md)
- Maintainer: [REDDIT](https://www.reddit.com/user/yorevs)
- Mailto: [HomeSetup](mailto:homesetup@gmail.com)

Enjoy!

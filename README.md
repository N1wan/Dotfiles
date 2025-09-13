# install instructions

- follow the arch wiki.
- install at least: pacstrap -K /mnt base linux linux-firmware git vim grub efibootmgr networkmanager
- make a user (useradd -m -G wheel user)
- set a password for the user (passwd user)
- switch user into the newly made one (su user)
- cd ~
- git clone https://github.com/N1wan/Dotfiles
- ./Dotfiles/install.sh

# git

for the git config make sure to add a ./private file next to the ./config file like this:
git
├── config
└── private

in this private file put something like:
[user]
    email = <your@email>
[sendemail]
    smtpserver = smtp.googlemail.com
    smtpencryption = tls
    smtpserverport = 587
    smtpuser = <your@email>
[credential]
    helper = store

#!/bin/bash

# updating system
sudo pacman -Syu --noconfirm

# getting yay
sudo pacman --noconfirm -S --needed base-devel git
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si
cd -
rm -rf yay

# installing programs
yay -S --noconfirm --needed --batchinstall acpi alsa-plugins alsa-utils amd-ucode arandr arch-install-scripts baobab base base-devel bash-completion batsignal bc bind blueman bluez bluez-utils bottom brightnessctl brillo catppuccin-gtk-theme-mocha clang composer curl dhcpcd dhcping dialog discord dmenu dmidecode dolphin dosfstools dunst e2fsprogs efibootmgr fastfetch fd feh firefox fzf gdb gimp git gnome-keyring google-gemini-cli grub haveged htop i3-wm i3blocks i3lock i3status imagemagick inetutils intellij-idea-ultimate-edition iw iwd java-environment-common java-runtime-common jdk-openjdk jdk21-openjdk julia kitty lazygit lib32-nvidia-utils lib32-systemd libqalculate libreoffice-fresh lightdm lightdm-gtk-greeter lightdm-gtk-greeter-settings lightdm-slick-greeter lightdm-webkit2-greeter linux linux-firmware linux-headers lshw luarocks lutris man-db man-pages maven micromamba-bin modelsim-intel-starter mokutil msmtp msmtp-mta mtr neovim net-tools network-manager-applet networkmanager nix nm-connection-editor nodejs nomacs noto-fonts noto-fonts-emoji npm ntfs-3g ntp nvidia-open nvidia-prime nvidia-settings openjdk-doc openssh optimus-manager-git os-prober pa-applet-git pacman-contrib pacseek pamixer papirus-icon-theme pavucontrol perl-authen-sasl perl-io-socket-ssl php pipewire pipewire-pulse powertop prismlauncher prismlauncher-themes-git python-conda python-eduvpn-client python-pip python-pynvim qemu-full qt5ct qt6ct quartus-free-devinfo-cyclone10lp quartus-free-quartus reflector ripgrep rofi ruby rust scrot signal-desktop steam sudo terminus-font texinfo thunderbird tigervnc timg tldr tlp tlp-rdw tmux tor torbrowser-launcher tree tree-sitter-cli ttf-dejavu ttf-droid ttf-jetbrains-mono-nerd ttf-liberation ttf-liberation-mono-nerd ttf-nerd-fonts-symbols-mono ttf-noto-nerd ttf-roboto ttf-ubuntu-font-family unclutter unzip upower vi vim vlc wget wine wireplumber wireshark-qt xclip xdg-user-dirs xorg-bdftopcf xorg-iceauth xorg-mkfontscale xorg-server xorg-sessreg xorg-setxkbmap xorg-smproxy xorg-x11perf xorg-xbacklight xorg-xcmsdb xorg-xcursorgen xorg-xdpyinfo xorg-xdriinfo xorg-xev xorg-xgamma xorg-xhost xorg-xinit xorg-xinput xorg-xkbcomp xorg-xkbevd xorg-xkbprint xorg-xkbutils xorg-xkill xorg-xlsatoms xorg-xlsclients xorg-xpr xorg-xrandr xorg-xrefresh xorg-xset xorg-xsetroot xorg-xvinfo xorg-xwd xorg-xwininfo xorg-xwud xsel yay zen-browser-bin zoxide zsh

# changing shell
chsh -s /usr/bin/zsh

# install tmux packages
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# symlinking config files
ln -s ~/Dotfiles/zsh/zshrc ~/.zshrc
ln -s ~/Dotfiles/zsh/p10k.zsh ~/.p10k.zsh
ln -s ~/Dotfiles/rofi ~/.config/rofi
ln -s ~/Dotfiles/nvim ~/.config/nvim
ln -s ~/Dotfiles/git ~/.config/git
ln -s ~/Dotfiles/tmux ~/.config/tmux
ln -s ~/Dotfiles/dunst ~/.config/dunst
ln -s ~/Dotfiles/i3 ~/.config/i3
ln -s ~/Dotfiles/fastfetch ~/.config/fastfetch
ln -s ~/Dotfiles/kitty ~/.config/kitty
ln -s ~/Dotfiles/resources/arch-black-4k ~/Dotfiles/resources/current_background

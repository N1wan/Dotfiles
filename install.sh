#!/bin/bash

# exit on error
set -e

# updating system
sudo pacman -Syu --noconfirm

# install yay if missing
if ! command -v yay &>/dev/null; then
    echo "[INFO] Installing yay..."
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    pushd /tmp/yay >/dev/null
    makepkg -si --noconfirm
    popd >/dev/null
    rm -rf /tmp/yay
else
    echo "[INFO] yay already installed."
fi

# installing programs
yay -S --noconfirm --needed --batchinstall acpi alsa-plugins alsa-utils amd-ucode arandr arch-install-scripts baobab base base-devel bash-completion batsignal bc bind blueman bluez bluez-utils bottom brightnessctl brillo catppuccin-gtk-theme-mocha clang composer curl dhcpcd dhcping dialog discord dmenu dmidecode dolphin dosfstools dunst e2fsprogs efibootmgr fastfetch fd feh firefox fzf gdb gimp git gnome-keyring google-gemini-cli grub haveged htop i3-wm i3blocks i3lock i3status imagemagick inetutils intellij-idea-ultimate-edition iw iwd java-environment-common java-runtime-common jdk-openjdk jdk21-openjdk julia kitty lazygit lib32-nvidia-utils lib32-systemd libqalculate libreoffice-fresh lightdm lightdm-gtk-greeter lightdm-gtk-greeter-settings lightdm-slick-greeter lightdm-webkit2-greeter linux linux-firmware linux-headers lshw luarocks lutris man-db man-pages maven micromamba-bin modelsim-intel-starter mokutil msmtp msmtp-mta mtr neovim net-tools network-manager-applet networkmanager nix nm-connection-editor nodejs nomacs npm ntfs-3g ntp nvidia-open nvidia-prime nvidia-settings openjdk-doc openssh optimus-manager-git os-prober pa-applet-git pacman-contrib pacseek pamixer pavucontrol perl-authen-sasl perl-io-socket-ssl php pipewire pipewire-pulse powertop prismlauncher prismlauncher-themes-git python-conda python-eduvpn-client python-pip python-pynvim qemu-full qt5ct qt6ct quartus-free-devinfo-cyclone10lp quartus-free-quartus reflector ripgrep rofi ruby rust scrot signal-desktop steam sudo texinfo thunderbird tigervnc timg tldr tlp tlp-rdw tmux tor torbrowser-launcher tree tree-sitter-cli unclutter unzip upower vi vim vlc wget wine wireplumber wireshark-qt xclip xdg-user-dirs xorg-bdftopcf xorg-iceauth xorg-mkfontscale xorg-server xorg-sessreg xorg-setxkbmap xorg-smproxy xorg-x11perf xorg-xbacklight xorg-xcmsdb xorg-xcursorgen xorg-xdpyinfo xorg-xdriinfo xorg-xev xorg-xgamma xorg-xhost xorg-xinit xorg-xinput xorg-xkbcomp xorg-xkbevd xorg-xkbprint xorg-xkbutils xorg-xkill xorg-xlsatoms xorg-xlsclients xorg-xpr xorg-xrandr xorg-xrefresh xorg-xset xorg-xsetroot xorg-xvinfo xorg-xwd xorg-xwininfo xorg-xwud xsel yay zen-browser-bin zoxide zsh

# installing fonts
yay -S --noconfirm --needed --batchinstall noto-fonts noto-fonts-emoji papirus-icon-theme terminus-font ttf-dejavu ttf-droid ttf-jetbrains-mono-nerd ttf-liberation ttf-liberation-mono-nerd ttf-nerd-fonts-symbols-mono ttf-noto-nerd ttf-roboto ttf-ubuntu-font-family 

# change shell (only if not already zsh)
if [ "$SHELL" != "/usr/bin/zsh" ]; then
    echo "[INFO] Changing shell to zsh..."
    chsh -s /usr/bin/zsh
else
    echo "[INFO] Shell already set to zsh."
fi

# enabling services
sudo systemctl enable NetworkManager.service

# install tmux packages
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# symlinking config files
ln -sfn ~/Dotfiles/zsh/zshrc ~/.zshrc
ln -sfn ~/Dotfiles/zsh/p10k.zsh ~/.p10k.zsh
ln -sfn ~/Dotfiles/rofi ~/.config/rofi
ln -sfn ~/Dotfiles/nvim ~/.config/nvim
ln -sfn ~/Dotfiles/git ~/.config/git
ln -sfn ~/Dotfiles/tmux ~/.config/tmux
ln -sfn ~/Dotfiles/dunst ~/.config/dunst
ln -sfn ~/Dotfiles/i3 ~/.config/i3
ln -sfn ~/Dotfiles/fastfetch ~/.config/fastfetch
ln -sfn ~/Dotfiles/kitty ~/.config/kitty

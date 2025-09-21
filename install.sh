#!/bin/bash

# exit on error
set -e

enable_multilib() {
    local conf="/etc/pacman.conf"

    # If [multilib] section is already enabled, do nothing
    if grep -q "^\[multilib\]" "$conf"; then
        echo "[INFO] multilib repo already enabled."
        return
    fi

    echo "[INFO] Enabling multilib repository..."
    sudo sed -i '/^\#\[multilib\]/,/Include/s/^#//' "$conf"
}

enable_multilib

# updating system
sudo pacman -Syyu --noconfirm

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

check_packages() {
    local all_pkgs
    local valid_pkgs=()
    local missing_pkgs=()

    # one big list of available packages
    all_pkgs=$(yay -Slq)

    for pkg in "$@"; do
        if grep -qx "$pkg" <<< "$all_pkgs"; then
            valid_pkgs+=("$pkg")
        else
            missing_pkgs+=("$pkg")
        fi
    done

    # # log missing packages
    # if ((${#missing_pkgs[@]} > 0)); then
    #     printf '%s\n' "${missing_pkgs[@]}" | tee -a ~/missing_packages.log
    # fi

    printf '%s\n' "${valid_pkgs[@]}"
}

# -------------------------
# categories
# -------------------------

PROGRAMS=(
  acpi alsa-plugins alsa-utils amd-ucode arandr arch-install-scripts baobab base base-devel
  batsignal bc bind blueman bluez bluez-utils bottom brightnessctl brillo catppuccin-gtk-theme-mocha
  clang composer curl dhcpcd dhcping dialog discord dmenu dmidecode dolphin dosfstools dunst
  e2fsprogs efibootmgr fastfetch fd feh firefox fzf gdb gimp git gnome-keyring grub
  haveged htop i3-wm i3blocks i3lock i3status imagemagick inetutils intellij-idea-ultimate-edition iw iwd
  java-environment-common java-runtime-common jdk-openjdk jdk21-openjdk kitty lazygit
  libreoffice-fresh lightdm lightdm-gtk-greeter lightdm-gtk-greeter-settings lightdm-slick-greeter
  lightdm-webkit2-greeter linux linux-firmware linux-headers lshw luarocks lutris man-db man-pages maven
  micromamba-bin mokutil msmtp msmtp-mta mtr neovim net-tools network-manager-applet
  networkmanager nix nm-connection-editor nodejs nomacs npm ntfs-3g ntp nvidia-open nvidia-prime nvidia-settings
  openssh optimus-manager-git os-prober pa-applet-git pacman-contrib pacseek pamixer pavucontrol perl-authen-sasl
  perl-io-socket-ssl php pipewire pipewire-pulse powertop prismlauncher prismlauncher-themes-git
  python-conda python-eduvpn-client python-pip python-pynvim qemu-full qt5ct qt6ct
  quartus-free-devinfo-cyclone10lp quartus-free-quartus modelsim-intel-starter 
  reflector ripgrep rofi ruby rust scrot
  signal-desktop steam sudo texinfo thunderbird tigervnc timg tldr tlp tlp-rdw tmux tor torbrowser-launcher
  tree tree-sitter-cli unclutter unzip upower vi vim vlc wget wine wireplumber wireshark-qt 
  xclip 
  xdg-user-dirs xorg-bdftopcf xorg-iceauth xorg-mkfontscale xorg-server xorg-sessreg xorg-setxkbmap xorg-smproxy
  xorg-x11perf xorg-xbacklight xorg-xcmsdb xorg-xcursorgen xorg-xdpyinfo xorg-xdriinfo xorg-xev xorg-xgamma
  xorg-xhost xorg-xinit xorg-xinput xorg-xkbcomp xorg-xkbevd xorg-xkbprint xorg-xkbutils xorg-xkill
  xorg-xlsatoms xorg-xlsclients xorg-xpr xorg-xrandr xorg-xrefresh xorg-xset xorg-xsetroot xorg-xvinfo
  xorg-xwd xorg-xwininfo xorg-xwud 
  yay zen-browser-bin zoxide zsh
)

FONTS=(
  noto-fonts noto-fonts-emoji papirus-icon-theme terminus-font
  ttf-dejavu ttf-droid ttf-jetbrains-mono-nerd ttf-liberation
  ttf-liberation-mono-nerd ttf-nerd-fonts-symbols-mono ttf-noto-nerd
  ttf-roboto ttf-ubuntu-font-family
)

# You can add more categories here:
# DEV_TOOLS=( docker docker-compose postgresql )
# GAMES=( minecraft-launcher heroic-games-launcher )

# -------------------------
# combine categories
# -------------------------

ALL_PACKAGES=(
  "${PROGRAMS[@]}"
  "${FONTS[@]}"
  # "${DEV_TOOLS[@]}"
  # "${GAMES[@]}"
)

# -------------------------
# filter + install
# -------------------------

VALID_PACKAGES=($(check_packages "${ALL_PACKAGES[@]}"))

if ((${#VALID_PACKAGES[@]} > 0)); then
    yay -S --noconfirm --needed --batchinstall "${VALID_PACKAGES[@]}"
else
    echo "[ERROR] No valid packages found. Check your package list."
    exit 1
fi

# change shell (only if not already zsh)
if [ "$SHELL" != "/usr/bin/zsh" ]; then
    echo "[INFO] Changing shell to zsh..."
    chsh -s /usr/bin/zsh
else
    echo "[INFO] Shell already set to zsh."
fi

# install tmux packages
if [ -d "$HOME/.tmux/plugins/tpm" ]; then
    echo "[INFO] tmux tpm already cloned."
else
  echo "[INFO] Cloning tpm..."
  git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
fi

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
# also to root
sudo mkdir -p /usr/share/backgrounds
sudo rm /usr/share/backgrounds/current_background
sudo cp ~/Dotfiles/resources/current_background /usr/share/backgrounds/current_background
sudo ln -sfn ~/Dotfiles/lightdm/* /etc/lightdm/
sudo mkdir -p /root/.config
sudo ln -sfn ~/Dotfiles/nvim /root/.config/nvim

enable_grub_theme() {
    local conf="/etc/default/grub"

    # If GRUB_THEME section is already enabled, do nothing
    if grep -q "^GRUB_THEME" "$conf"; then
        echo "[INFO] grub theme already enabled."
        return
    fi

    echo "[INFO] Enabling grub theme..."

    git clone https://github.com/catppuccin/grub.git /tmp/grub_catppuccin
    pushd /tmp/grub_catppuccin >/dev/null
    sudo cp -r src/* /usr/share/grub/themes/
    popd >/dev/null
    rm -rf /tmp/grub_catppuccin
    sudo sed -i 's|^#GRUB_THEME=.*|GRUB_THEME=/usr/share/grub/themes/catppuccin-mocha-grub-theme/theme.txt|' "$conf"
    sudo grub-mkconfig -o /boot/grub/grub.cfg
}
enable_grub_theme

# enabling services
sudo systemctl enable --now NetworkManager.service
sudo systemctl enable --now lightdm.service

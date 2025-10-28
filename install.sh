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

# -------------------------
# categories
# -------------------------

DEVELOPMENT=(
    docker docker-compose
    java-environment-common java-runtime-common jdk-openjdk 
    jdk21-openjdk maven nodejs npm python-pip ruby rust
)

DRIVERS=(
    lib32-mesa mesa nvidia-open lib32-nvidia-utils nvidia-utils
    nvidia-settings amd-ucode
)

SYSTEM=(
    base base-devel bluez acpi alsa-utils alsa-plugins 
    dhcpcd dosfstools e2fsprogs efibootmgr gnome-keyring grub 
    linux linux-firmware linux-headers networkmanager ntp 
    openssh os-prober pipewire pipewire-pulse xf86-video-nouveau
    qt5ct qt6ct sudo tlp tor wireplumber xdg-user-dirs xorg
)

TOOLS=(
    bluez-utils arch-install-scripts clang dunst fzf luarocks 
    man-db man-pages network-manager-applet pacman-contrib 
    pamixer reflector scrot tree-sitter-cli unclutter upower

    yay xclip zsh zoxide blueman batsignal bc brillo bottom curl
    fastfetch feh gdb git htop lazygit neovim pacseek qemu-full 
    ripgrep timg tldr tmux tree unzip vi vim wget wine
)

PROGRAMS=(
    arandr baobab discord dolphin gimp kitty libreoffice-fresh 
    lutris pavucontrol prismlauncher prismlauncher-themes-git 
    python-eduvpn-client qbittorrent rofi signal-desktop steam 
    thunderbird tigervnc torbrowser-launcher vlc zen-browser-bin
)

FONTS=(
    noto-fonts noto-fonts-emoji papirus-icon-theme terminus-font
    ttf-dejavu ttf-droid ttf-jetbrains-mono-nerd ttf-liberation
    ttf-liberation-mono-nerd ttf-nerd-fonts-symbols-mono ttf-noto-nerd
    ttf-roboto ttf-ubuntu-font-family
)

DISPLAY_MANAGERS=( 
    lightdm lightdm-gtk-greeter lightdm-slick-greeter
)

WINDOW_MANAGERS=( 
    i3-wm i3blocks 
)

# -------------------------
# combine categories
# -------------------------

ALL_PACKAGES=(
    "${DEVELOPMENT[@]}"
    "${DRIVERS[@]}"
    "${SYSTEM[@]}"
    "${TOOLS[@]}"
    "${PROGRAMS[@]}"
    "${FONTS[@]}"
    "${DISPLAY_MANAGERS[@]}"
    "${WINDOW_MANAGERS[@]}"
)

# -------------------------
# install
# -------------------------
yay -S --noconfirm --needed "${ALL_PACKAGES[@]}" || {
  echo "[WARN] Some packages failed. Retrying individually..."
  for pkg in "${ALL_PACKAGES[@]}"; do
      yay -S --noconfirm --needed "$pkg" || echo "[ERROR] Failed to install $pkg"
  done
}

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
ln -sfn ~/Dotfiles/xorg/xprofile ~/.xprofile
ln -sfn ~/Dotfiles/zsh/zshrc ~/.zshrc
ln -sfn ~/Dotfiles/zsh/p10k.zsh ~/.p10k.zsh
ln -sfn ~/Dotfiles/qt/qt5ct ~/.config/qt5ct
ln -sfn ~/Dotfiles/qt/qt6ct ~/.config/qt6ct
ln -sfn ~/Dotfiles/rofi ~/.config/rofi
ln -sfn ~/Dotfiles/nvim ~/.config/nvim
ln -sfn ~/Dotfiles/git ~/.config/git
ln -sfn ~/Dotfiles/tmux ~/.config/tmux
ln -sfn ~/Dotfiles/dunst ~/.config/dunst
ln -sfn ~/Dotfiles/i3 ~/.config/i3
ln -sfn ~/Dotfiles/session/* ~/.config/session
ln -sfn ~/Dotfiles/fastfetch ~/.config/fastfetch
ln -sfn ~/Dotfiles/kitty ~/.config/kitty
# also to root
sudo ln -sfn ~/Dotfiles/environment/global /etc/environment
sudo mkdir -p /usr/share/backgrounds
sudo rm -f /usr/share/backgrounds/current_background
sudo cp ~/Dotfiles/resources/current_background /usr/share/backgrounds/current_background
sudo mkdir -p /etc/lightdm/
sudo ln -sfn ~/Dotfiles/lightdm/* /etc/lightdm/
sudo mkdir -p /root/.config
sudo ln -sfn ~/Dotfiles/nvim /root/.config/nvim
sudo mkdir -p /etc/X11/xorg.conf.d/
sudo ln -sfn ~/Dotfiles/Xorg/00-keyboard.conf /etc/X11/xorg.conf.d/00-keyboard.conf

# make lightdm work
chmod o+rx ~/Dotfiles/lightdm/*
chmod o+rx ~/Dotfiles/lightdm
chmod o+rx ~/Dotfiles
chmod o+rx ~

# make Xorg work
chmod o+rx ~/Dotfiles/Xorg/*
chmod o+rx ~/Dotfiles/Xorg

# make screenshots work
mkdir -p ~/Pictures/Screenshots

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

# groups
# docker group:
if getent group docker >/dev/null; then
    if groups "$USER" | grep -qw docker; then
        echo "[INFO] User '$USER' already in docker group."
    else
        echo "[INFO] Adding user '$USER' to docker group..."
        sudo usermod -aG docker "$USER"
        echo "[INFO] You may need to log out and back in for changes to take effect."
    fi
else
    echo "[INFO] Creating docker group and adding user '$USER'..."
    sudo groupadd docker
    sudo usermod -aG docker "$USER"
    echo "[INFO] You may need to log out and back in for changes to take effect."
fi
# video group:
if getent group video >/dev/null; then
    if groups "$USER" | grep -qw video; then
        echo "[INFO] User '$USER' already in video group."
    else
        echo "[INFO] Adding user '$USER' to video group..."
        sudo usermod -aG video "$USER"
        echo "[INFO] You may need to log out and back in for changes to take effect."
    fi
else
    echo "[INFO] Creating video group and adding user '$USER'..."
    sudo groupadd video
    sudo usermod -aG video "$USER"
    echo "[INFO] You may need to log out and back in for changes to take effect."
fi

# enabling services
sudo systemctl enable --now tlp.service
sudo systemctl mask systemd-rfkill.service
sudo systemctl mask systemd-rfkill.socket
sudo systemctl enable --now NetworkManager.service
sudo systemctl enable --now bluetooth.service
sudo systemctl enable --now ntpd.service
sudo systemctl enable --now docker.socket
systemctl enable --now --user wireplumber.service
sudo systemctl enable --now lightdm.service

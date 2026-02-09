#!/bin/bash
set -euo pipefail

if ! command -v sudo &>/dev/null; then
    echo "[ERROR] sudo not found. Install it first."
    exit 1
fi
sudo -v

# enable multilib
if ! grep -q "^\[multilib\]" /etc/pacman.conf; then
    echo "[INFO] Enabling multilib repository..."
    sudo sed -i '/\[multilib\]/,/Include/{s/^#//}' /etc/pacman.conf
    sudo pacman -Sy
fi

# Add hooks to mkinitcpio.conf
CURRENT_HOOKS=$(grep -E '^HOOKS=' "/etc/mkinitcpio.conf" | sed 's/[[:space:]]*$//')
DESIRED_HOOKS='HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block filesystems resume fsck)'
# Replace only if different
if [[ "$CURRENT_HOOKS" != "$DESIRED_HOOKS" ]]; then
    echo "[INFO] Updating HOOKS line in /etc/mkinitcpio.conf"
    sudo sed -i -E "s|^HOOKS=.*|$DESIRED_HOOKS|" "/etc/mkinitcpio.conf"
    sudo mkinitcpio -P
fi

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
fi

# Define packages in their correct category
DEVELOPMENT=(
    docker docker-compose
    java-environment-common java-runtime-common jdk-openjdk 
    jdk21-openjdk maven nodejs npm python-pip ruby rustup
)

DRIVERS=(
    lib32-mesa mesa nvidia-open lib32-nvidia-utils nvidia-utils
    nvidia-settings amd-ucode
)

SYSTEM=(
    base base-devel bluez acpi alsa-utils alsa-plugins udiskie udisks2
    dhcpcd dosfstools e2fsprogs efibootmgr gnome-keyring grub 
    linux linux-firmware linux-headers networkmanager ntp 
    openssh os-prober pipewire pipewire-pulse xf86-video-nouveau
    qt5ct qt6ct sudo tlp tor wireplumber xdg-user-dirs xorg sassc
)

TOOLS=(
    bluez-utils arch-install-scripts clang dunst fzf luarocks 
    man-db man-pages network-manager-applet pacman-contrib 
    pamixer reflector scrot tree-sitter-cli unclutter upower
	gnome-themes-extra

    yay xclip zsh zoxide blueman batsignal bc brillo bottom curl
    fastfetch feh gdb git htop lazygit neovim pacseek qemu-full 
    ripgrep timg tldr tmux tree unzip vi vim wget wine redshift 
	gtk-engine-murrine
)

PROGRAMS=(
    arandr baobab discord dolphin gimp kitty libreoffice-fresh localsend
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

# Combine packages
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

# install
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
fi

# install tmux packages
if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
    echo "[INFO] Cloning tpm..."
    git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
fi

# Enable the GRUB_THEME
if ! grep -q "^GRUB_THEME" "/etc/default/grub"; then
    echo "[INFO] Enabling grub theme..."

    git clone https://github.com/catppuccin/grub.git /tmp/grub_catppuccin
    pushd /tmp/grub_catppuccin >/dev/null
    sudo cp -r src/* /usr/share/grub/themes/
    popd >/dev/null
    rm -rf /tmp/grub_catppuccin
    sudo sed -i 's|^#GRUB_THEME=.*|GRUB_THEME=/usr/share/grub/themes/catppuccin-mocha-grub-theme/theme.txt|' "/etc/default/grub"
    sudo grub-mkconfig -o /boot/grub/grub.cfg
fi

add_user_to_group() {
    local group="$1"

    # create group if it doesn't exist
    if ! getent group "$group" >/dev/null; then
        echo "[INFO] Creating '$group' group..."
        sudo groupadd "$group"
    fi

    # add user to group if not already a member
    if ! groups "$USER" | grep -qw "$group"; then
        echo "[INFO] Adding user '$USER' to '$group' group..."
        sudo usermod -aG "$group" "$USER"
    fi
}
add_user_to_group docker
add_user_to_group video

# symlinking config files
ln -sfn ~/Dotfiles/Xorg/Xresources ~/.Xresources
ln -sfn ~/Dotfiles/zsh/zshrc ~/.zshrc
ln -sfn ~/Dotfiles/zsh/p10k.zsh ~/.p10k.zsh
ln -sfn ~/Dotfiles/qt/qt5ct ~/.config/qt5ct
ln -sfn ~/Dotfiles/qt/qt6ct ~/.config/qt6ct
ln -sfn ~/Dotfiles/rofi ~/.config/rofi
ln -sfn ~/Dotfiles/picom ~/.config/picom
ln -sfn ~/Dotfiles/nvim ~/.config/nvim
ln -sfn ~/Dotfiles/git ~/.config/git
ln -sfn ~/Dotfiles/gtk/gtk4 ~/.config/'gtk-4.0'
ln -sfn ~/Dotfiles/gtk/gtk3/themes ~/.themes
ln -sfn ~/Dotfiles/gtk/gtk3/config ~/.config/'gtk-3.0'
ln -sfn ~/Dotfiles/tmux ~/.config/tmux
ln -sfn ~/Dotfiles/dunst ~/.config/dunst
ln -sfn ~/Dotfiles/i3 ~/.config/i3
mkdir -p ~/.config/session
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

# allow gnome-keyring-daemon to lock memory pages that store secrets
sudo setcap cap_ipc_lock=+ep /usr/bin/gnome-keyring-daemon

# automatically configure xorg
sudo nvidia-xconfig

# enabling services
sudo systemctl enable --now tlp.service
sudo systemctl mask systemd-rfkill.service
sudo systemctl mask systemd-rfkill.socket
sudo systemctl enable --now NetworkManager.service
sudo systemctl enable --now bluetooth.service
sudo systemctl enable --now udisks2.service
sudo systemctl enable --now ntpd.service
sudo systemctl enable --now docker.socket
systemctl enable --now --user wireplumber.service
sudo systemctl enable --now lightdm.service

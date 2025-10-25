# install instructions

- ip link
    - (connect to the internet)
    - iwctl device list
    - iwctl station DEVICE scan
    - iwctl station DEVICE get-networks
    - iwctl station DEVICE connect SSID
- ping ping.archlinux.org
- timedatectl
- cfdisk
- mkfs.ext4 /dev/root_partition
- mkfs.fat -F 32 /dev/efi_partition
- mkswap /dev/swap_partition
- mount /dev/root_partition /mnt
- mount --mkdir /dev/efi_partition /mnt/boot
- swapon /dev/swap_partition
- pacman -Sy
- pacstrap -K /mnt base base-devel linux linux-firmware grub efibootmgr sudo networkmanager git vi vim
- genfstab -U /mnt >> /mnt/etc/fstab
- arch-chroot /mnt
- ln -sf /usr/share/zoneinfo/Region/City /etc/localtime
- hwclock --systohc
- vim /etc/locale.gen
    - uncomment "en_US.UTF-8 UTF-8"
- locale-gen
- vim /etc/locale.conf
    - add (LANG=en_US.UTF-8)
- vim /etc/hostname
    - add your hostname
- passwd
- grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
- grub-mkconfig -o /boot/grub/grub.cfg
- exit
- reboot

- visudo /etc/sudoers
    - uncomment to allow all members of group wheel to execute any command
- make a user (useradd -m -G wheel user)
- set a password for the user (passwd user)
- switch user into the newly made one (su user)
- cd ~
- sudo systemctl enable --now NetworkManager.service
- connect to a network (nmtui)
- (git clone https://github.com/N1wan/Dotfiles.git) or if you have ssh access (git clone git@github.com:N1wan/Dotfiles.git)
- Dotfiles/install.sh

# dual booting
mount the other operating systems bootloader partition.
turn on os_prober in /etc/default/grub
rerun grub-mkconfig -o /boot/grub/grub.cfg
(make sure any time grub-mkconfig is ran, the other operating system is mounted)

# git

to create an ssh key:
ssh-keygen -t ed25519 -C "your_email@example.com"
then add it in github

for the git config make sure to add a ./private file next to the ./config file like this:
git
├── config
└── private

in this private file put something like:
[user]
    email = <your@email>
[sendemail]
    smtpuser = <your@email>

# tmux

install packages with prefix -> Shift+i

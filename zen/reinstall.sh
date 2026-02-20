mkdir -p ~/.config/zen
rm -rf ~/.config/zen/*

mkdir ~/.config/zen/my_profile

ln -sfn ~/Dotfiles/zen/profiles.ini ~/.config/zen
ln -sfn ~/Dotfiles/zen/installs.ini ~/.config/zen
ln -sfn ~/Dotfiles/zen/user.js ~/.config/zen/my_profile

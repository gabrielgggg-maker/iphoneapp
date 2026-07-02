import 'dart:math';

// Lewd/ecchi lines sprinkled across the app. Cat-flavored for Kooteu ;)
const lewdPhrases = [
  'Nya~ Kooteu, come see what this kitty hid just for you 😳',
  'Download me slow... or fast, the way a curious cat likes it 💦',
  'Collect these treats and make this kitty arch her back 🔞',
  'Shhh... this stays between us cats, okay? 😈',
  'Nothing is naughtier than this search, except you, Kooteu 😏',
  'Already purring, just waiting for you to press play~',
  'Careful: spicy +18 catnip all over here 🥵',
  'Pet me... I mean, tap the image 💋',
  'One more cutie for your secret little litter 😻',
  'You are the kind of cat who likes to see it all, right Kooteu? 👀',
  'Choose well, Kooteu, this kitty earned your paws 💕',
  'Saved and curled up nice and close to you, nya~',
];

String randomLewd() => lewdPhrases[Random().nextInt(lewdPhrases.length)];

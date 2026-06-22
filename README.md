# mtcaptcha-solver

<img width="794" height="229" alt="image" src="https://github.com/user-attachments/assets/508c1f1d-a9e1-46cd-9671-8899978c7822" />

# Deobfuscation Process

I started by using the demo found on the 2captcha website. When analyzing the network requests, this is what we see:

<img width="425" height="314" alt="image" src="https://github.com/user-attachments/assets/801b59fd-b9bb-4014-bc80-e2737fd1ed2a" />

The first request (highlighted in pink) is a GET request made to MTCaptcha that fetches the actual CAPTCHA JavaScript, which also contains the iframe logic itself.

After that, the script calls the `mtcv1/api/getchallenge.json` endpoint (highlighted in orange). This returns a challenge issued by the server that must be solved by the client-side JavaScript.

Once the challenge has been computed, the result is used to fetch the CAPTCHA image (highlighted in yellow) by calling `/getimage.json`.

The image is then processed using an OCR model. In this implementation, I've used DeepInfra's API with the Qwen model for simplicity. Feel free to use a local OCR solution or train your own model for a cheaper and faster alternative.

Finally, we submit the answer along with `fa`, `kt`, and `fs` (the original fold seed) to `/solvechallenge.json` (highlighted in green). The response contains a `vt` (verification token), which can be validated using 2Captcha's verification endpoint.

## JavaScript Deobfuscation

The JavaScript obfuscation is relatively minimal and mostly consists of string obfuscation.

The function `function _0x27c6()` contains the string table:

<img width="556" height="445" alt="image" src="https://github.com/user-attachments/assets/a789d25d-c5b1-491c-a141-18045d87e4c4" />

A rotator function is then used to determine the correct index for each string lookup:

<img width="571" height="202" alt="image" src="https://github.com/user-attachments/assets/f01f52ec-43c2-499a-befc-43ba5fa2254b" />

Once identified, Babel was used to automatically replace all instances of these lookups with their actual values from the string table.

For example:

```js
Math[_0x5839(0x2e3)](
    Date[_0x5839(0x2a9)]()
)
```

becomes:

```js
Math.floor(Date.now())
```

After replacing the remaining lookups, we identified the fold algorithm responsible for completing the initial challenge (the one required before the image can be retrieved):

```js
FoldChlg: {
  URLSafeBase64CharCode2IntMap: [...],
  URLSafeBase64Int2CharMap: [...],
  solve: function (...) { ... },
  foldBase64IntArray: function (...) { ... },
  ...
}
```

## Understanding the Fold Algorithm

The fold algorithm works as follows:

1. Decode the seed into an array of integers (`0-63`) using the URL-safe Base64 alphabet.
2. Repeat `fslots` times:

   1. Apply `foldBase64IntArray` 31 times.
   2. Apply the same fold operation `fdepth` additional times on the result.
   3. Hash the array using `hashIntAry` (a signed 32-bit integer hash).
   4. Take the hash modulo `4096` and encode it as two Base64 characters (`4096 = 64²`).
   5. Append those two characters to the output.
3. Return the concatenated string.

The returned value is `fa`, and without it the server rejects the request used to retrieve the CAPTCHA image.

## Solving the Challenge

After obtaining the image and computing the fold answer, we submit the following parameters to `/solvechallenge.json`:

| Parameter | Description                                                               |
| --------- | ------------------------------------------------------------------------- |
| `ct`      | The challenge token obtained from the initial challenge request.          |
| `st`      | The CAPTCHA solution (text read from the CAPTCHA image).                  |
| `fa`      | The fold answer (proof-of-work value computed from the fold seed).        |
| `kt`      | Keystroke data used to simulate user typing behavior.                     |
| `fs`      | The original fold seed returned by the challenge endpoint.                |
| `lf`      | Indicates whether the challenge is low-friction (`0` = normal challenge). |
| `sk`      | The site key associated with the CAPTCHA instance.                        |
| `bd`      | The domain on which the CAPTCHA is being solved.                          |
| `rt`      | Request timestamp in milliseconds since the Unix epoch.                   |
| `tsh`     | Transaction signature: `TH[MD5("mtcap@mtcaptcha.com" + sitekey)]`.        |
| `ss`      | Session identifier generated for each solve attempt.                      |

The response contains a verification token (`vt`) which can then be validated using the verification endpoint.

## Contact

https://t.me/yaziraof

# Android Quiz Engine

This folder contains the Kotlin implementation of the strict TAH quiz binary format.

Each record is decoded as:

1. Little-endian unsigned 16-bit question byte length.
2. UTF-8 question bytes.
3. Four repeated little-endian unsigned 16-bit answer byte lengths plus UTF-8 answer bytes.
4. One correct-answer byte, restricted to `0..3`.

`QuizBinaryParser.loadAllQuestions` reads concatenated records until the buffer is exhausted.
`QuizController` provides an endless shuffle bag and a deterministic daily challenge seeded as
`yyyyMMdd`.

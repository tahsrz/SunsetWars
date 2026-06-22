package com.sunsetwars.quiz

import java.nio.BufferUnderflowException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.time.LocalDate
import java.util.Collections
import java.util.Random

data class QuizItem(
    val question: String,
    val answers: List<String>,
    val correctIndex: Int
) {
    init {
        require(answers.size == ANSWER_COUNT) { "QuizItem requires exactly $ANSWER_COUNT answers." }
        require(correctIndex in 0 until ANSWER_COUNT) { "correctIndex must be 0, 1, 2, or 3." }
    }

    companion object {
        const val ANSWER_COUNT = 4
    }
}

class QuizParseException(message: String, cause: Throwable? = null) : IllegalArgumentException(message, cause)

object QuizBinaryParser {
    private const val SHORT_BYTE_COUNT = 2
    private const val BYTE_COUNT = 1

    fun parseFourChoiceQuestion(buffer: ByteBuffer): QuizItem {
        buffer.order(ByteOrder.LITTLE_ENDIAN)

        return try {
            val questionText = readUtf8String(buffer, "question")
            val answers = List(QuizItem.ANSWER_COUNT) { index ->
                readUtf8String(buffer, "answer $index")
            }
            val correctIndex = readCorrectIndex(buffer)

            QuizItem(questionText, answers, correctIndex)
        } catch (error: BufferUnderflowException) {
            throw QuizParseException("Truncated quiz item at byte ${buffer.position()}.", error)
        }
    }

    fun loadAllQuestions(binaryData: ByteArray): List<QuizItem> {
        val buffer = ByteBuffer.wrap(binaryData).order(ByteOrder.LITTLE_ENDIAN)
        val questions = mutableListOf<QuizItem>()

        while (buffer.hasRemaining()) {
            questions.add(parseFourChoiceQuestion(buffer))
        }

        return questions
    }

    private fun readUtf8String(buffer: ByteBuffer, label: String): String {
        ensureRemaining(buffer, SHORT_BYTE_COUNT, "$label length")

        val length = buffer.short.toInt() and 0xffff
        ensureRemaining(buffer, length, label)

        val bytes = ByteArray(length)
        buffer.get(bytes)
        return String(bytes, Charsets.UTF_8)
    }

    private fun readCorrectIndex(buffer: ByteBuffer): Int {
        ensureRemaining(buffer, BYTE_COUNT, "correct index")

        val correctIndex = buffer.get().toInt() and 0xff
        if (correctIndex !in 0 until QuizItem.ANSWER_COUNT) {
            throw QuizParseException("Correct index must be 0, 1, 2, or 3; found $correctIndex.")
        }
        return correctIndex
    }

    private fun ensureRemaining(buffer: ByteBuffer, byteCount: Int, label: String) {
        if (buffer.remaining() < byteCount) {
            throw QuizParseException(
                "Truncated $label at byte ${buffer.position()}: need $byteCount bytes, " +
                    "have ${buffer.remaining()}."
            )
        }
    }
}

fun parseFourChoiceQuestion(buffer: ByteBuffer): QuizItem =
    QuizBinaryParser.parseFourChoiceQuestion(buffer)

fun loadAllQuestions(binaryData: ByteArray): List<QuizItem> =
    QuizBinaryParser.loadAllQuestions(binaryData)

class QuizController(
    private val allQuestions: List<QuizItem>,
    private val todayProvider: () -> LocalDate = { LocalDate.now() }
) {
    private var activeDeck = shuffledQuestions()

    init {
        require(allQuestions.isNotEmpty()) { "QuizController requires at least one question." }
    }

    fun getNextRandom(): QuizItem {
        if (activeDeck.isEmpty()) {
            activeDeck = shuffledQuestions()
        }
        return activeDeck.removeAt(0)
    }

    fun getDailyQuestions(count: Int = 10): List<QuizItem> {
        require(count >= 0) { "count must be non-negative." }

        val today = todayProvider()
        val seed = (today.year * 10000 + today.monthValue * 100 + today.dayOfMonth).toLong()
        val dailyDeck = allQuestions.toMutableList()
        Collections.shuffle(dailyDeck, Random(seed))
        return dailyDeck.take(count)
    }

    private fun shuffledQuestions(): MutableList<QuizItem> =
        allQuestions.toMutableList().also { Collections.shuffle(it) }
}

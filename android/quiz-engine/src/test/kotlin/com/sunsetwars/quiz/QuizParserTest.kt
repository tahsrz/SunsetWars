package com.sunsetwars.quiz

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.time.LocalDate
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class QuizParserTest {
    @Test
    fun parsesSingleFourChoiceQuestion() {
        val item = parseFourChoiceQuestion(
            encodedQuestion(
                question = "Capital of Texas?",
                answers = listOf("Austin", "Dallas", "Houston", "Waco"),
                correctIndex = 0
            )
        )

        assertEquals("Capital of Texas?", item.question)
        assertEquals(listOf("Austin", "Dallas", "Houston", "Waco"), item.answers)
        assertEquals(0, item.correctIndex)
    }

    @Test
    fun loadsAllConcatenatedQuestions() {
        val first = encodedQuestion("One?", listOf("A", "B", "C", "D"), 2).array()
        val second = encodedQuestion("Two?", listOf("E", "F", "G", "H"), 3).array()

        val loaded = loadAllQuestions(first + second)

        assertEquals(2, loaded.size)
        assertEquals("One?", loaded[0].question)
        assertEquals(2, loaded[0].correctIndex)
        assertEquals("Two?", loaded[1].question)
        assertEquals(3, loaded[1].correctIndex)
    }

    @Test
    fun rejectsInvalidCorrectIndex() {
        val buffer = encodedQuestion("Bad?", listOf("A", "B", "C", "D"), 4)

        assertFailsWith<QuizParseException> {
            parseFourChoiceQuestion(buffer)
        }
    }

    @Test
    fun rejectsTruncatedPayload() {
        val data = encodedQuestion("Cut?", listOf("A", "B", "C", "D"), 1).array().dropLast(1).toByteArray()

        assertFailsWith<QuizParseException> {
            loadAllQuestions(data)
        }
    }

    @Test
    fun dailyQuestionsAreDateSeeded() {
        val questions = (0 until 12).map { index ->
            QuizItem(
                question = "Question $index",
                answers = listOf("A", "B", "C", "D"),
                correctIndex = index % 4
            )
        }
        val controllerA = QuizController(questions) { LocalDate.of(2026, 6, 21) }
        val controllerB = QuizController(questions) { LocalDate.of(2026, 6, 21) }

        assertEquals(controllerA.getDailyQuestions(), controllerB.getDailyQuestions())
        assertEquals(10, controllerA.getDailyQuestions().size)
    }

    private fun encodedQuestion(question: String, answers: List<String>, correctIndex: Int): ByteBuffer {
        require(answers.size == 4)

        val fields = listOf(question) + answers
        val byteCount = fields.sumOf { 2 + it.toByteArray(Charsets.UTF_8).size } + 1
        val buffer = ByteBuffer.allocate(byteCount).order(ByteOrder.LITTLE_ENDIAN)

        fields.forEach { value ->
            val bytes = value.toByteArray(Charsets.UTF_8)
            buffer.putShort(bytes.size.toShort())
            buffer.put(bytes)
        }
        buffer.put(correctIndex.toByte())
        buffer.flip()
        return buffer
    }
}

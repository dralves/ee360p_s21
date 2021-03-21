import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.RepeatedTest;
import org.junit.jupiter.api.Test;

import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class TestPriorityQueue {

    final static int QUEUE_SIZE = 250;

    // Tests the basic (non-concurrent) functionality of PriorityQueue
    // to insert and remove from the queue.
    @Test
    public void testBasicAddAndRemove() throws Exception {
        PriorityQueue queue = new PriorityQueue(10);
        assertEquals(0, queue.add("A", 0));
        assertEquals(0, queue.add("B", 9));
        assertEquals(1, queue.add("C", 5));
        assertEquals("B", queue.getFirst());
        assertEquals("C", queue.getFirst());
        assertEquals("A", queue.getFirst());
    }

    // Tests that the queue returns the right thing when the elements
    // are already present.
    @Test
    public void testAlreadyPresent() throws Exception {
        PriorityQueue queue = new PriorityQueue(10);
        assertEquals(0, queue.add("A", 0));
        assertEquals(-1, queue.add("A", 0));
        assertEquals(1, queue.add("B", 0));
        assertEquals(-1, queue.add("B", 0));
    }

    // Tests that the queue returns the right position on search.
    @Test
    public void testSearch() throws Exception {
        PriorityQueue queue = new PriorityQueue(10);
        assertEquals(-1, queue.search("A"));
        assertEquals(0, queue.add("A", 0));
        assertEquals(0, queue.add("B", 9));
        assertEquals(1, queue.add("C", 5));
        assertEquals(0, queue.search("B"));
        assertEquals(1, queue.search("C"));
        assertEquals(2, queue.search("A"));
        queue.getFirst();
        queue.getFirst();
        queue.getFirst();
        assertEquals(-1, queue.search("A"));
    }

    // Tests that the queue validates the priority by not inserting the elements.
    // @Test
    public void testValidatesPriority() throws Exception {
        PriorityQueue queue = new PriorityQueue(10);
        try {
            queue.add("A", -1);
        } catch (Throwable t) {
        }
        assertEquals(-1, queue.search("A"));
        try {
            queue.add("B", 10);
        } catch (Throwable t) {
        }
        assertEquals(-1, queue.search("B"));
    }

    // Tests that the queue blocks when it's full.
    @Test
    public void testBlocksOnFull() throws Exception {
        PriorityQueue queue = new PriorityQueue(2);
        assertEquals(0, queue.add("A", 0));
        assertEquals(0, queue.add("B", 1));
        Thread thread = new Thread(new Runnable() {
                public void run() {
                    try {
                        queue.add("C", 9);
                    } catch (Exception e) {}
                }
            });
        thread.start();
        Thread.sleep(500);
        // C shouldn't be there
        assertEquals(-1, queue.search("C"));
        // C should be inserted if we remove B
        assertEquals("B", queue.getFirst());
        thread.join();
        // C should now be first.
        assertEquals("C", queue.getFirst());
        assertEquals("A", queue.getFirst());
    }

    // Tests that the queue blocks when it's empty.
    @Test
    public void testBlocksOnEmpty() throws Exception {
        PriorityQueue queue = new PriorityQueue(10);
        Thread thread = new Thread(new Runnable() {
                public void run() {
                    // If the queue does the right thing
                    // this blocks until there is an element.
                    try {
                        queue.getFirst();
                    } catch (Exception e) {}
                }
            });
        thread.start();
        assertEquals(0, queue.add("A", 0));
        // Sleep a little
        Thread.sleep(500);
        // A shouldn't be there anymore.
        assertEquals(-1, queue.search("A"));
    }

    // Tests the queue with two inserter threads and one remover, first the inserters
    // insert in parallel, the the remover is added, then the inserters are stopped
    // and the remover is expected to drain the queue. At the end the queue should
    // have 0 elements.
    @Test
    public void testMultiThreadedInsertAndRemove() throws Exception {
        AtomicInteger counter = new AtomicInteger();
        AtomicBoolean shutdown = new AtomicBoolean(false);
        ExecutorService inserter_pool = Executors.newCachedThreadPool();
        ExecutorService remover_pool = Executors.newCachedThreadPool();
        Random generator = new Random();
        PriorityQueue queue = new PriorityQueue(10000);

        // Add two inserters, which will eventually block.
        inserter_pool.submit(new Runnable() {
                public void run() {
                    while (!shutdown.get()) {
                        String next = Integer.toString(generator.nextInt(1000));
                        try {
                            queue.add(next, generator.nextInt(10));
                        } catch (Exception e) {return;}
                        counter.getAndIncrement();
                    }
                }
            });
        inserter_pool.submit(new Runnable() {
                public void run() {
                    while (!shutdown.get()) {
                        String next = Integer.toString(generator.nextInt(1000));
                        try {
                            queue.add(next, generator.nextInt(10));
                        } catch (Exception e) {return;}
                        counter.getAndIncrement();
                    }
                }
            });

        // Sleep a bit.
        Thread.sleep(1000);

        // Now add a remover.
        Future remover = remover_pool.submit(new Runnable() {
                public void run() {
                    while(true) {
                        try {
                            queue.getFirst();
                        } catch (Exception e) {return;}
                        counter.getAndDecrement();
                    }
                }
            });

        // Sleep a bit.
        Thread.sleep(500);
        // Now tell the inserters to shutdonw, that should eventually make the remover
        // remove all the items.
        shutdown.set(true);
        inserter_pool.shutdownNow();
        inserter_pool.awaitTermination(3, TimeUnit.SECONDS);

        // The removers should have a chance to consume all the items.
        Thread.sleep(5000);
        assertEquals(0, counter.get());

        remover_pool.shutdownNow();
        remover_pool.awaitTermination(3, TimeUnit.SECONDS);
    }
}

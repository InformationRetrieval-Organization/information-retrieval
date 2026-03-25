import React, { useState, useEffect } from "react";
import { Button, Card, CardHeader, CardContent, Link } from "@heroui/react";

function truncateContent(content: string, wordLimit: number) {
    const words = content.split(' ');
    if (words.length > wordLimit) {
        return words.slice(0, wordLimit).join(' ') + '...';
    } else {
        return content;
    }
}

export default function ResultsList({ results }: { results: ArticleResult[] }) {
    const [currentPage, setCurrentPage] = useState(1);
    const [searchPerformed, setSearchPerformed] = useState(false);
    const [initialRender, setInitialRender] = useState(true);
    const resultsPerPage = 10;
    const totalPages = Math.max(1, Math.ceil(results.length / resultsPerPage));

    // Calculate the range of results for the current page
    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;
    const resultsForPage = results.slice(startIndex, endIndex);

    // On the initial render, it sets initialRender to false.
    // On subsequent renders (when results change), it sets searchPerformed to true.
    useEffect(() => {
        if (initialRender) {
            setInitialRender(false);
        } else {
            setSearchPerformed(true);
            setCurrentPage(1);
        }
    }, [results]);

    // If the search was performed and no results were found, display a message
    if (searchPerformed && results.length === 0) {
        return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Nothing found</div>
    }

    return (
        <div>
            {resultsForPage.map((result, index) => (
                <Card key={index} className="mt-3">
                    <CardHeader className="flex gap-3">
                        <div className="flex flex-col">
                            <p className="text-md">
                                <Link
                                    href={result.link}
                                    target="_blank"
                                    rel="noreferrer noopener"
                                >
                                    {result.title}
                                </Link>
                            </p>
                        </div>
                        <p>{new Date(result.published_on).toLocaleDateString()}</p>
                    </CardHeader>
                    <CardContent className="px-3 py-0 text-small text-default-400 mb-2">
                        <p>{truncateContent(result.content, 20)}</p>
                    </CardContent>
                </Card>
            ))}
            {results.length > resultsPerPage && (
                <div className="mt-4 flex items-center justify-center gap-3">
                    <Button
                        variant="secondary"
                        isDisabled={currentPage <= 1}
                        onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                    >
                        Previous
                    </Button>

                    <span className="text-sm text-default-500">
                        Page {currentPage} of {totalPages}
                    </span>

                    <Button
                        variant="secondary"
                        isDisabled={currentPage >= totalPages}
                        onClick={() =>
                            setCurrentPage((page) => Math.min(totalPages, page + 1))
                        }
                    >
                        Next
                    </Button>
                </div>
            )}
        </div>
    );
}
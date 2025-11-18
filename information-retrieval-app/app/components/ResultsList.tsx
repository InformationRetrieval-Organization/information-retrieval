import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardBody, Link, Pagination } from "@heroui/react";

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
                                    isExternal
                                    showAnchorIcon
                                    href={result.link}>
                                    {result.title}
                                </Link>
                            </p>
                        </div>
                        <p>{new Date(result.published_on).toLocaleDateString()}</p>
                    </CardHeader>
                    <CardBody className="px-3 py-0 text-small text-default-400 mb-2">
                        <p>{truncateContent(result.content, 20)}</p>
                    </CardBody>
                </Card>
            ))}
            <Pagination
                className="mt-3"
                total={Math.ceil(results.length / resultsPerPage)}
                initialPage={1}
                onChange={(page) => setCurrentPage(page)}
            />
        </div>
    );
}
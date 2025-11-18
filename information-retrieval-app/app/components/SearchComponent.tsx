"use client";
import React, { useEffect, useState } from "react";
import { Button, Divider, Input } from "@heroui/react";
import { SearchIcon } from "../../components/icons";
import ResultsList from "./ResultsList";
import AdvancedFilter from "./AdvancedFilter";
import { getBooleanArticles, getVectorSpaceArticles } from '../api/information_retrieval';

const SearchComponent = ({ searchType }: { searchType: string }) => {
    const [inputValue, setInputValue] = useState("");
    const [results, setResults] = useState<ArticleResult[]>([]);
    const [filters, setFilters] = useState<Filter[]>([{ operator: "AND", value: "" }]);
    const [isLoading, setIsLoading] = useState(false);

    const fetchData = async () => {
        setIsLoading(true);

        try {
            let url = '';
            let data: ArticleResult[] = [];

            if (searchType === 'vector-space') {
                url = `/search/${searchType}?q=${inputValue.replace(/\s/g, '+')}`;
                data = await getVectorSpaceArticles(url);
            } else if (searchType === 'boolean') {
                url = `/search/${searchType}`;
                const body = [{ operator: "AND", value: inputValue }, ...filters];
                data = await getBooleanArticles(url, body);
            }

            setResults(data);
        } catch (error) {
            console.error("Failed to fetch data:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <section className="flex flex-col gap-5 m-8">
            <div className="flex items-center gap-2">
                <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="search term"
                    size="md"
                    type="search"
                />

                <Button isIconOnly color="primary" variant="solid" size="lg" onClick={fetchData} isLoading={isLoading}>
                    <SearchIcon size={18} />
                </Button>
            </div>

            {searchType === 'boolean' && <AdvancedFilter filters={filters} setFilters={setFilters} />}

            <Divider />

            <ResultsList results={results} />
        </section>
    );
}

export default SearchComponent;
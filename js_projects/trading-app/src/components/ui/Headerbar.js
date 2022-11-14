import React from "react";
import SearchBar from "../form/Searchbar";
import styled from "styled-components";
import MailImage from "../../assets/img/email.png"

export default function Headerbar(){
    return (<Header className = 'header'>
        <SearchBarContainer className = 'search-bar-container'>
            <SearchBar className="search-bar" type="search"/>
            <Image></Image>
        </SearchBarContainer>
    </Header>)
}

// Define styled headerbar
const Header = styled.div`
    height: 2rem;
    min-height: 2rem;
    width: 100vw;
    background-color: #14283c;
`
// Define styled headerbar
const SearchBarContainer = styled.div`
    display: flex;
    justify-content: end;
    align-items:center;
    padding-right: 1vw;
    height: 2rem;
    min-height: 2rem;
    width: 80vw;
    border-bottom: 0.5px solid white;
    border-right: 0.5px solid white;
`

const Image = styled.img`
    margin-left: 1vw;
    height: 1.5rem;
    width: 1.5rem;
    margin-top: 0.2rem;
`

Image.defaultProps = {
    src: MailImage,
}

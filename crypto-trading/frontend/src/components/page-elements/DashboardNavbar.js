import React, {useState} from "react";
import styled from 'styled-components'
import { Link } from 'react-router-dom';
import StockTicks from "../../assets/img/stocks.svg"
import BurgerMenu from "../../assets/img/menu.svg"

export default function DashboardNavbar(){
    const [barOpened, setBarOpened] = useState(false)

    return (
        <Navbar className = "dashboard-navbar" bar-opened = {barOpened}>
            <BurgerMenuImg src= {BurgerMenu} onClick = {event => setBarOpened(!barOpened)}></BurgerMenuImg>
            <Link to="/test"><Image src= {StockTicks}></Image></Link>
            <Link to="/test"><Image src= {StockTicks}></Image></Link>
            <Link to="/test"><Image src= {StockTicks}></Image></Link>
            <Link to="/test"><Image src= {StockTicks}></Image></Link>
        </Navbar>)
}

const Navbar = styled.div`
    padding: 1rem;
    padding-top: 10vh;
    background-color: black;
    min-height: 40%;
    height: 100%;
    width: 10vw;
    display: flex;
    flex-direction: column;
    gap: 10vh;
    align-items: center;
`

const BurgerMenuImg = styled.img`
    height: 2rem;
    width: 2rem;
`

BurgerMenuImg.defaultProps = {
    src: BurgerMenu,
}

const Image = styled.img`
    height: 3rem;
    width: 3rem;
    filter: ${props => (props.isActive ? "grayscale(0%)" :"grayscale(100%)")};
`

Image.defaultProps = {
    src: StockTicks,
}
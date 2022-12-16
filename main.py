import numpy as np
import matplotlib.pyplot as plt
import datetime as date
import copy
from ctypes import *


class DistributionParameters():
    # среднеквадратичное отклонение
    scale = 0
    # средний коэффициент массонакопления
    massAccumulationCoefficient = 0
    # количество рыб
    amountFishes = 0
    # массив значений, которые распределены по Гауссу в заданных параметрах
    _gaussValues = []

    def __init__(self, amountFishes,
                 scale=0.003,
                 massAccumulationCoefficientMin=0.07,
                 massAccumulationCoefficientMax=0.087):
        self.massAccumulationCoefficient = (massAccumulationCoefficientMin +
                                       massAccumulationCoefficientMax) / 2
        self.amountFishes = amountFishes
        self.scale = scale
        self._make_gaussian_distribution()

    def _make_gaussian_distribution(self):
        self._gaussValues = np.random.normal(self.massAccumulationCoefficient,
                                        self.scale,
                                        self.amountFishes)
        self._gaussValues.sort()

    def draw_hist_distribution(self, numberFishInOneColumn):
        plt.hist(self._gaussValues, numberFishInOneColumn)
        plt.show()

    def return_array_distributed_values(self):
        return self._gaussValues


def assemble_array(array, amountItems, index):
    result = (c_float * amountItems)()
    for i in range(amountItems):
        result[i] = array[i][index]
    return result


def calculate_end_date_of_month(startDate):
    '''
    result = startDate
    while ((result.day != startDate.day) or
           (result.month == startDate.month)):
        result += date.timedelta(1)
    '''
    month = startDate.month + 1
    year = startDate.year
    if (year > 2100):
        print('Опять ошибка с датами((((((((((((((((((((((((((((')
    if (month > 12):
        month = 1
        year += 1
    result = date.date(year, month, startDate.day)
    return result


def draw_line(start, end, step, current):
    amount = int((end - start) / step)
    percent = current / amount * 100
    print(int(percent), '%')


class FishArray():
    _amountFishes = 0
    _arrayFishes = list()
    _biomass = c_float()
    # массив покупок мальков
    _arrayFryPurchases = list()
    _feedRatio = 1.5
    _dllBuisnessPlan = 0


    def __init__(self, feedRatio=1.5):
        self._feedRatio = c_float(feedRatio)
        self._biomass = c_float()
        self._amountFishes = 0
        self._arrayFishes = list()
        self._arrayFryPurchases = list()
        self._dllBuisnessPlan = WinDLL('D:/github/business_v1.3/Project1/x64/Debug/dllArrayFish.dll')

    def add_biomass(self, date, amountFishes, averageMass):
        # создаем параметры для нормального распределения коэффициентов массонакопления
        distributionParameters = DistributionParameters(amountFishes)
        arrayCoefficients = distributionParameters.return_array_distributed_values()

        # закидываем информацию о новой биомассе в массив
        for i in range(amountFishes):
            # ноль означает (количество дней в бассике, но это не точно
            # arrayFishes = [[startingMass, massAccumulationCoefficient, currentMass],...]
            self._arrayFishes.append([averageMass, arrayCoefficients[i], averageMass])
            self._arrayFryPurchases.append([date, amountFishes, averageMass])

        # увеличиваем количество рыбы в бассейне
        self._amountFishes += amountFishes
        # так как все в граммах, то делим на 1000, чтобы получить килограммы в биомассе
        self._biomass.value += amountFishes * averageMass / 1000

    def add_other_FishArrays(self, fishArray):
        amountNewFishes = len(fishArray)

        # arrayFishes = [[startingMass, massAccumulationCoefficient, currentMass]
        for i in range(amountNewFishes):
            self._biomass.value = self._biomass.value + fishArray[i][2] / 1000
            self._arrayFishes.append(fishArray[i])
        self._amountFishes += amountNewFishes

    def _sort_fish_array(self):
        self._arrayFishes.sort(key=lambda x: x[2])

    def remove_biomass(self, amountFishToRemove):
        self._sort_fish_array()
        removedFishes = list()
        for i in range(amountFishToRemove):
            fish = self._arrayFishes.pop(self._amountFishes - amountFishToRemove)
            removedFishes.append(fish)
            # уменьшаем биомассу
            self._biomass.value -= fish[2] / 1000
        # уменьшаем количество рыб
        self._amountFishes -= amountFishToRemove
        return removedFishes

    def daily_work(self):
        # подготовим переменные для использования ctypes
        dailyWorkLib = self._dllBuisnessPlan.daily_work

        dailyWorkLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float)]
        dailyWorkLib.restype = c_float

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)

        dailyFeedMass = dailyWorkLib(arrayMass, arrayMassAccumulationCoefficient,
                                     self._amountFishes, self._feedRatio,
                                     byref(self._biomass))

        for i in range(self._amountFishes):
            self._arrayFishes[i][2] = arrayMass[i]

        return dailyFeedMass

    def do_daily_work_some_days(self, amountDays):
        # подготовим переменные для использования ctypes
        dailyWorkLib = self._dllBuisnessPlan.do_daily_work_some_days

        dailyWorkLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float), c_int]
        dailyWorkLib.restype = c_float

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)

        totalFeedMass = dailyWorkLib(arrayMass, arrayMassAccumulationCoefficient,
                                     self._amountFishes, self._feedRatio,
                                     byref(self._biomass), amountDays)

        for i in range(self._amountFishes):
            self._arrayFishes[i][2] = arrayMass[i]

        return totalFeedMass

    def get_amount_fishes(self):
        return self._amountFishes

    def get_array_fish(self):
        return self._arrayFishes

    def calculate_when_fish_will_be_sold(self, massComercialFish,
                                         singleVolume, fishArray):
        # подготовим переменные для использования ctypes
        calculateLib = self._dllBuisnessPlan.calculate_when_fish_will_be_sold

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float),
                                 c_float, c_int]
        calculateLib.restype = c_int

        amountFish = len(fishArray)
        biomass = 0
        for i in range(amountFish):
            biomass += fishArray[i][2] / 1000
        biomass = c_float(biomass)

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(fishArray, amountFish, 2)
        arrayMassAccumulationCoefficient = assemble_array(fishArray,
                                                          amountFish, 1)

        amountDays = calculateLib(arrayMass, arrayMassAccumulationCoefficient,
                                  amountFish, self._feedRatio,
                                  byref(biomass), massComercialFish,
                                  singleVolume)

        for i in range(amountFish):
            fishArray[i][2] = arrayMass[i]

        return amountDays

    def calculate_difference_between_number_growth_days_and_limit_days(self, massComercialFish, singleVolume,
                                                                       maxDensity, square):
        calculateLib = self._dllBuisnessPlan.calculate_how_many_fish_needs

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 POINTER(c_float), c_int, c_float,
                                 POINTER(c_float),  POINTER(c_float),
                                 c_float, c_int, c_float, c_float,
                                 POINTER(c_int)]
        calculateLib.restype = c_int

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass1 = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMass2 = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)
        resultAmountsDays = (c_int * 2)(0)

        biomass1 = c_float(0.0)
        biomass2 = c_float(0.0)

        for i in range(self._amountFishes):
            biomass1.value += arrayMass1[i] / 1000
            biomass2.value += arrayMass1[i] / 1000

        amountDays = calculateLib(arrayMass1, arrayMass2, arrayMassAccumulationCoefficient,
                                  self._amountFishes, self._feedRatio,
                                  byref(biomass1), byref(biomass2), massComercialFish,
                                  singleVolume, maxDensity, square, resultAmountsDays)

        return [amountDays, resultAmountsDays[0], resultAmountsDays[1]]
    def calculate_average_mass(self):
        self.update_biomass()
        if (self._amountFishes != 0):
            result = self._biomass.value / self._amountFishes * 1000
        else:
            result = 0.0
        return result

    def update_biomass(self):
        result = 0
        for i in range(self._amountFishes):
            result += self._arrayFishes[i][2] / 1000
        self._biomass.value = result

    def get_biomass(self):
        return self._biomass.value

    def get_three_fish(self):
        result = [[self._arrayFishes[0][1], self._arrayFishes[0][2]]]
        middle = int(self._amountFishes / 2)
        result.append([self._arrayFishes[middle][1], self._arrayFishes[middle][2]])
        end = self._amountFishes - 1
        result.append([self._arrayFishes[end][1], self._arrayFishes[end][2]])
        return result


class Pool():
    square = 0
    maxPlantingDensity = 0
    arrayFishes = 0
    # количество мальков в 1 упаковке
    singleVolumeFish = 0
    # цена на мальков
    costFishFry = [[5, 35],
                   [10, 40],
                   [20, 45],
                   [30, 50],
                   [50, 60],
                   [100, 130]]
    # массив, в котором хранится информация о покупке мальков
    arrayFryPurchases = list()
    # массив, в котором хранится информация о продаже рыбы
    arraySoldFish = list()
    # текущая плотность посадки
    currentDensity = 0
    # массив кормежек
    feeding = list()
    # масса товарной рыбы
    massComercialFish = 350
    # цена рыбы
    price = 1000
    # индекс зарыбления
    indexFry = 0
    # начальная масса зарыбления
    startMass = 0
    procentOnDepreciationEquipment = 10
    poolHistory = list()


    def __init__(self, square, startMass, singleVolumeFish=100, price=850,
                 massComercialFish=350,
                 maximumPlantingDensity=40):
        self.square = square
        self.startMass = startMass
        self.massComercialFish = massComercialFish
        self.maxPlantingDensity = maximumPlantingDensity
        self.singleVolumeFish = singleVolumeFish
        self.arrayFishes = FishArray()
        self.feeding = list()
        self.arrayFryPurchases = list()
        self.arraySoldFish = list()
        self.poolHistory = list()
        self.price = price

    def add_new_biomass(self, amountFishes, averageMass, newIndex, date):
        self.indexFry = newIndex
        self.arrayFishes.add_biomass(date, amountFishes, averageMass)
        # сохраним инфо о покупки мальков
        # arrayFryPurchases[i] = [date, amountFries, averageMass, totalPrice]
        totalPrice = 0
        for i in range(1, len(self.costFishFry)):
            if (self.costFishFry[i - 1][0] < averageMass <= self.costFishFry[i][0]):
                totalPrice = amountFishes * self.costFishFry[i][1]
                break
            elif (averageMass > 200):
                totalPrice = amountFishes * averageMass
                break
        self.arrayFryPurchases.append([date, amountFishes, averageMass, totalPrice])
        self.currentDensity = amountFishes * (averageMass / 1000) / self.square

    def daily_growth(self, day, saveInfo):
        todayFeedMass = self.arrayFishes.daily_work()
        # сохраняем массы кормежек
        self.feeding.append([day, todayFeedMass])

        # проверяем, есть ли рыба на продажу, и если есть - продаем
        self.sell_fish(day)
        if (saveInfo):
            # [день, количество рыбы, биомасса, средняя масса, плотность]
            self.poolHistory.append([day, self.arrayFishes.get_amount_fishes(), self.arrayFishes.get_biomass(),
                                     self.arrayFishes.calculate_average_mass(), self.update_density()])

    def sell_fish(self, day):
        amountFishForSale = 0
        for i in range(self.arrayFishes.get_amount_fishes()):
            if (self.arrayFishes.get_array_fish()[i][2] >= self.massComercialFish):
                amountFishForSale += 1

        if ((amountFishForSale >= self.singleVolumeFish) or
                ((amountFishForSale == self.arrayFishes.get_amount_fishes()) and
                 (self.arrayFishes.get_amount_fishes() != 0))):
            previousBiomass = self.arrayFishes.get_biomass()
            soldFish = self.arrayFishes.remove_biomass(amountFishForSale)
            # продаем выросшую рыбу и сохраняем об этом инфу
            soldBiomass = 0
            amountSoldFish = 0
            for i in range(len(soldFish)):
                soldBiomass += soldFish[i][2] / 1000
                amountSoldFish += 1

            revenue = soldBiomass * self.price

            self.arraySoldFish.append([day, amountSoldFish, soldBiomass, revenue])
            # обновим density
            self.currentDensity = self.arrayFishes.get_biomass() / self.square
            '''
            print(day, ' indexFry = ', self.indexFry, ' было ', previousBiomass, ' продано: ', soldBiomass,
                  ' стало ', self.arrayFishes.get_biomass(), ' выручка: ', revenue)
            '''

    def update_density(self):
        self.currentDensity = self.arrayFishes.get_biomass() / self.square
        return self.currentDensity

    def calculate_difference_between_number_growth_days_and_limit_days(self, amountFishForSale):
        testFishArray = copy.deepcopy(self.arrayFishes)
        amountDays = testFishArray.calculate_difference_between_number_growth_days_and_limit_days\
            (self.massComercialFish,
             amountFishForSale,
             self.maxPlantingDensity,
             self.square)
        return amountDays


class Opimization():
    _dllArrayFish = 0
    _dllPool = 0

    def __init__(self):
        self._dllPool = WinDLL("D:/github/buisnessPlan_v1.2.1/buisnessPlan_v1.2/dllPool/x64/Debug/dllPool.dll")
        self._dllArrayFish = WinDLL('D:/github/business_v1.3/Project1/x64/Debug/dllArrayFish.dll')

    def calculate_optimized_amount_fish_in_commercial_pool(self, square, startMass, mass, startAmount, step):
        flagNumber = 0
        amountFish = startAmount
        amountGrowthDays = 0
        amountDaysBeforeLimit = 0

        while (flagNumber >= 0):
            pool = Pool(square, startMass)
            pool.add_new_biomass(amountFish, mass, 0, date.date.today())
            x = pool.calculate_difference_between_number_growth_days_and_limit_days(amountFish)
            flagNumber = x[0]
            if (flagNumber >= 0):
                amountFish += step
                amountGrowthDays = x[1]
                amountDaysBeforeLimit = x[2]

        return [amountFish, amountGrowthDays, amountDaysBeforeLimit]

    def calculate_max_average_mass(self, square, maxDensity, amountDays, startMass, step, amountFish, feedRatio):
        # подготовим переменные для использования ctypes
        calculateLib = self._dllArrayFish.calculate_density_after_some_days

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float),
                                 c_int, c_float]
        calculateLib.restype = c_float

        currentMass = startMass
        currentDensity = 0
        while(currentDensity < maxDensity):
            # созданим объект FishArray
            fishArray = FishArray()
            fishArray.add_biomass(date.date.today(), amountFish, currentMass)
            # соберем массивы масс и коэффициентов массонакопления
            arrayMass = assemble_array(fishArray.get_array_fish(), amountFish, 2)
            arrayMassAccumulationCoefficient = assemble_array(fishArray.get_array_fish(),
                                                              amountFish, 1)

            biomass = c_float(0.0)
            for i in range(amountFish):
                biomass.value += arrayMass[i] / 1000

            currentDensity = calculateLib(arrayMass, arrayMassAccumulationCoefficient,
                                      amountFish, feedRatio,
                                      byref(biomass), amountDays,
                                      square)
            if (currentDensity < maxDensity):
                currentMass += step

        return currentMass

    def calculate_optimal_deltaMass(self, masses, startDelta, step, endDelta, startDate, endDate):
        delta = startDelta
        max = 0
        result = delta
        encounter = 1
        while (delta <= endDelta):
            cwsd = CWSD(masses, 2, 4, 10, 2, 260, 40000, 2, 5.5, 3.17, 70000, 3000000, 10, 18)
            cwsd.work_cwsd(startDate, endDate, 50, delta)
            x = cwsd.calculate_result_business_plan(startDate, endDate)
            if (max < x):
                max = x
                result = delta
            delta += step
            draw_line(startDelta, endDelta, step, encounter)
            print([delta, x])
            encounter += 1
        return [result, max]

    def calculate_optimal_credit(self, masses, startCredit, step, endCredit, startDate, endDate):
        credit = startCredit
        min = 0
        result = credit
        encounter = 1
        while (credit <= endCredit):
            cwsd = CWSD(masses, 2, 4, 10, 2, 260, 40000, 2, 5.5, 3.17, 70000, 3000000,
                        7.5, 7.5, credit, 15, 12, 9 * credit)
            cwsd.work_cwsd(startDate, endDate, 50, 50)
            cwsd.calculate_result_business_plan(startDate, endDate)
            x = cwsd.find_minimal_budget()
            if ((x > 0) and (x > min)):
                min = x
                result = credit
            draw_line(startCredit, endCredit, step, encounter)
            print([credit, x])
            encounter += 1
            credit += step
        return [result, min]


class Module():
    costCWSD = 3000000
    amountPools = 0
    # температура воды
    temperature = 21
    # арендная плата
    rent = 70000
    # стоимость киловатт в час
    costElectricityPerHour = 3.17
    # мощность узв
    equipmentCapacity = 5.6
    # стоимость корма
    feedPrice = 260
    onePoolSquare = 0
    correctionFactor = 2
    pools = list()
    poolsInfo = list()


    def __init__(self, poolSquare, masses, amountPools=4, correctionFactor=2):
        self.onePoolSquare = poolSquare
        self.amountPools = amountPools
        self.correctionFactor = correctionFactor
        self.pools = list()
        self.poolsInfo = list()

        for i in range(amountPools):
            pool = Pool(poolSquare, masses[i])
            self.pools.append(pool)

    def add_biomass_in_pool(self, poolNumber, amountFishes, mass, newIndex, date):
        self.pools[poolNumber].add_new_biomass(amountFishes, mass, newIndex, date)

    def move_fish_from_one_pool_to_another(self, onePoolNumber, anotherPoolNumber, amountMovedFish):
        # удалим выросшую рыбу из старого бассейна
        removedFish = self.pools[onePoolNumber].arrayFishes.remove_biomass(amountMovedFish)
        # обновим плотность
        self.pools[onePoolNumber].update_density()
        # добавим удаленную рыбу в другой бассейн
        self.pools[anotherPoolNumber].arrayFishes.add_other_FishArrays(removedFish)
        # обновим плотность в другом бассейне
        self.pools[anotherPoolNumber].update_density()
        # теперь в новом бассейне плавает малек с индексом из предыдущего басса
        self.pools[anotherPoolNumber].indexFry = self.pools[onePoolNumber].indexFry

    def total_daily_work(self, day, save_pool_info):
        for i in range(self.amountPools):
            self.pools[i].daily_growth(day, save_pool_info)

    def print_info(self):
        print()
        for i in range(self.amountPools):
            print('№', i, ' бассейн, indexFry = ', self.pools[i].indexFry, ', количество рыбы = ',
                  self.pools[i].arrayFishes.get_amount_fishes(),
                  ', биомасса = ', self.pools[i].arrayFishes.get_biomass(),
                  ', средняя масса = ', self.pools[i].arrayFishes.calculate_average_mass(),
                  ', плотность = ', self.pools[i].update_density())
            if (self.pools[i].arrayFishes.get_amount_fishes() != 0):
                # выпишем данные о первых amoutItemes рыбках
                print(self.pools[i].arrayFishes.get_three_fish())
            else:
                print('Рыбы нет')
        print('_______________________________________________________')

    def find_optimal_fry_mass(self, minMass, deltaMass):
        minAverageMass = 10000
        for i in range(self.amountPools):
            averageMassInThisPool = self.pools[i].arrayFishes.calculate_average_mass()
            if ((minAverageMass > averageMassInThisPool) and (averageMassInThisPool > 0)):
                minAverageMass = averageMassInThisPool

        result = (int((minAverageMass - deltaMass) / 10)) * 10
        if (result < minMass):
            result = minMass

        return result

    def find_empty_pool_and_add_one_volume(self, volumeFish, newIndex, day, deltaMass):
        maxAverageMass = 0
        emptyPool = 0
        for i in range(self.amountPools):
            if ((self.pools[i].arrayFishes.get_amount_fishes() == 0) and
                    (self.pools[i].startMass > maxAverageMass)):
                maxAverageMass = self.pools[i].startMass
                emptyPool = i

        optimalMass = self.find_optimal_fry_mass(20, deltaMass)
        self.pools[emptyPool].add_new_biomass(volumeFish, optimalMass, newIndex, day)

    def find_empty_pool_and_add_twice_volume(self, volumeFish, newIndex, day, koef, deltaMass):
        emptyPool = 0
        for i in range(self.amountPools):
            if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                emptyPool = i
                break

        optimalMass = self.find_optimal_fry_mass(20, deltaMass)
        self.pools[emptyPool].add_new_biomass(int(koef * volumeFish), optimalMass, newIndex, day)

    def find_pool_with_twice_volume_and_move_half_in_empty(self, day):
        overflowingPool = 0
        emptyPool = 0
        maxAmount = 0
        volumeFish = 0
        maxAverageMass = 0
        for i in range(self.amountPools):
            if (self.pools[i].arrayFishes.get_amount_fishes() > maxAmount):
                overflowingPool = i
                maxAmount = self.pools[i].arrayFishes.get_amount_fishes()

            volumeFish = int(maxAmount / 2)

            if ((self.pools[i].arrayFishes.get_amount_fishes() == 0) and
                    (maxAverageMass < self.pools[i].startMass)):
                emptyPool = i
                maxAverageMass = self.pools[i].startMass

        self.move_fish_from_one_pool_to_another(overflowingPool, emptyPool, volumeFish)

    def grow_up_fish_in_one_pool(self, startDay, startDateSaving):
        flag = True
        day = startDay
        currentDateSaving = startDateSaving

        while (flag):
            while (currentDateSaving < day):
                currentDateSaving = calculate_end_date_of_month(currentDateSaving)

            if (currentDateSaving == day):
                needSave = True
                currentDateSaving = calculate_end_date_of_month(currentDateSaving)
            else:
                needSave = False

            self.total_daily_work(day, needSave)
            day += date.timedelta(1)
            for i in range(self.amountPools):
                if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                    flag = False
                    break

        return day

    def grow_up_fish_in_two_pools(self, startDay, startDateSaving):
        flag = True
        day = startDay
        currentDateSaving = startDateSaving

        while(flag):
            while (currentDateSaving < day):
                currentDateSaving = calculate_end_date_of_month(currentDateSaving)

            if (currentDateSaving == day):
                needSave = True
                currentDateSaving = calculate_end_date_of_month(currentDateSaving)
                x = currentDateSaving
                y = day

            else:
                needSave = False

            self.total_daily_work(day, needSave)
            day += date.timedelta(1)

            amountEmptyPools = 0
            for i in range(self.amountPools):
                if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                    amountEmptyPools += 1

            if (amountEmptyPools >= 2):
                flag = False

        return day

    def start_script1(self, masses, reserve, startDate, koef, deltaMass):
        optimization = Opimization()
        optimalQuantity = optimization.calculate_optimized_amount_fish_in_commercial_pool(self.onePoolSquare,
                                                                                          masses[self.amountPools - 1],
                                                                                          masses[self.amountPools - 1],
                                                                                          10, 10)
        mainVolumeFish = optimalQuantity[0]
        mainVolumeFish -= reserve

        for i in range(self.amountPools - 1):
            self.pools[i].add_new_biomass(mainVolumeFish, masses[i], i, startDate)
        # в бассейн с самой легкой рыбой отправляем в koef раз больше
        self.pools[self.amountPools - 1].indexFry = self.amountPools - 1
        self.pools[self.amountPools - 1].add_new_biomass(int(koef * mainVolumeFish), masses[self.amountPools - 1],
                                                          self.amountPools - 1, startDate)

        day = startDate

        # вырастим рыбу в 0 бассейне
        day = self.grow_up_fish_in_one_pool(day, startDate)

        # переместим рыбу из 3 в 0 бассейн
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)

        # вырастим рыбу в 1 бассейне
        day = self.grow_up_fish_in_one_pool(day, startDate)

        currentIndex = 4

        # добавим рыбу 2 * mainValue в 1 бассейн
        self.find_empty_pool_and_add_twice_volume(mainVolumeFish, currentIndex, day, koef, deltaMass)
        currentIndex += 1

        # вырастим рыбу в 2 бассейне
        day = self.grow_up_fish_in_one_pool(day, startDate)

        return [mainVolumeFish, day, currentIndex]

    def main_script1(self, mainValue, day, previousIndex, startDateSaving, koef, deltaMass):
        # переместим из переполненного бассейна в пустой половину
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)

        # вырастим рыбу в 2 бассейнах
        day = self.grow_up_fish_in_two_pools(day, startDateSaving)

        currentIndex = previousIndex
        # добавим mainValue штук рыб в пустой бассейн
        self.find_empty_pool_and_add_one_volume(mainValue, currentIndex, day, deltaMass)
        currentIndex += 1

        # добавим koef * mainValue штук рыб в другой пустой бассейн
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day, koef, deltaMass)
        currentIndex += 1

        # вырастим рыбу в 2 бассейнах
        day = self.grow_up_fish_in_two_pools(day, startDateSaving)

        # переместим из переполненного бассейна в пустой
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)

        # добавим 2 * mainValue штук рыб в другой пустой бассейн
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day, koef, deltaMass)
        currentIndex += 1

        # вырастим рыбу в 1 бассейне
        day = self.grow_up_fish_in_one_pool(day, startDateSaving)

        return [mainValue, day, currentIndex]

    def main_work1(self, startDate, endDate, masses, reserve, deltaMass):
        resultStartScript = self.start_script1(masses, reserve, startDate, self.correctionFactor, deltaMass)

        day = resultStartScript[1]
        # [mainVolumeFish, day, currentIndex]
        resultMainScript = self.main_script1(resultStartScript[0],
                                             resultStartScript[1],
                                             resultStartScript[2],
                                             startDate, self.correctionFactor, deltaMass)

        numberMainScript = 2
        while (day < endDate):
            numberMainScript += 1
            # [mainValue, day, currentIndex]
            resultMainScript = self.main_script1(resultMainScript[0],
                                                 resultMainScript[1],
                                                 resultMainScript[2],
                                                 startDate, self.correctionFactor, deltaMass)
            day = resultMainScript[1]

    def start_script_with_print(self, masses, reserve, startDate, koef, deltaMass):
        optimization = Opimization()
        optimalQuantity = optimization.calculate_optimized_amount_fish_in_commercial_pool(self.onePoolSquare,
                                                                                          masses[self.amountPools - 1],
                                                                                          masses[self.amountPools - 1],
                                                                                          10, 10)
        mainVolumeFish = optimalQuantity[0]
        mainVolumeFish -= reserve
        print('Оптимальное количество мальков в 1 бассейн: ', mainVolumeFish)

        print('Сделаем первое зарыбление ', startDate)
        for i in range(self.amountPools - 1):
            self.pools[i].add_new_biomass(mainVolumeFish, masses[i], i, startDate)
        # в бассейн с самой легкой рыбой отправляем в koef раз больше
        self.pools[self.amountPools - 1].indexFry = self.amountPools - 1
        self.pools[self.amountPools - 1].add_new_biomass(int(koef * mainVolumeFish), masses[self.amountPools - 1],
                                                         self.amountPools - 1, startDate)
        self.print_info()

        day = startDate

        # вырастим рыбу в 0 бассейне
        print('вырастим рыбу в 0 бассейне')
        day = self.grow_up_fish_in_one_pool(day, startDate)
        print(day)
        self.print_info()

        # переместим рыбу из 3 в 0 бассейн
        print('переместим рыбу из 3 в 0 бассейн')
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)
        self.print_info()

        # вырастим рыбу в 1 бассейне
        print('вырастим рыбу в 1 бассейне')
        day = self.grow_up_fish_in_one_pool(day, startDate)
        print(day)
        self.print_info()

        currentIndex = 4

        # добавим рыбу 2 * mainValue в 1 бассейн
        print('добавим рыбу 2 * mainValue в 1 бассейн')
        self.find_empty_pool_and_add_twice_volume(mainVolumeFish, currentIndex, day, koef, deltaMass)
        self.print_info()
        currentIndex += 1

        # вырастим рыбу в 2 бассейне
        print('вырастим рыбу в 2 бассейне')
        day = self.grow_up_fish_in_one_pool(day, startDate)
        print(day)
        self.print_info()

        return [mainVolumeFish, day, currentIndex]

    def main_script_with_print(self, mainValue, day, previousIndex, startDateSaving, koef, deltaMass):
        # переместим из переполненного бассейна в пустой половину
        print('переместим из переполненного бассейна в пустой половину')
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)
        self.print_info()

        # вырастим рыбу в 2 бассейнах
        print('вырастим рыбу в 2 бассейнах')
        day = self.grow_up_fish_in_two_pools(day, startDateSaving)
        print(day)
        self.print_info()

        currentIndex = previousIndex
        # добавим mainValue штук рыб в пустой бассейн
        print('добавим mainValue штук рыб в пустой бассейн')
        self.find_empty_pool_and_add_one_volume(mainValue, currentIndex, day, deltaMass)
        self.print_info()
        currentIndex += 1

        # добавим koef * mainValue штук рыб в другой пустой бассейн
        print('добавим koef * mainValue штук рыб в другой пустой бассейн')
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day, koef, deltaMass)
        currentIndex += 1
        self.print_info()

        # вырастим рыбу в 2 бассейнах
        print('вырастим рыбу в 2 бассейнах')
        day = self.grow_up_fish_in_two_pools(day, startDateSaving)
        print(day)
        self.print_info()

        # переместим из переполненного бассейна в пустой
        print('переместим из переполненного бассейна в пустой')
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)
        self.print_info()

        # добавим 2 * mainValue штук рыб в другой пустой бассейн
        print('добавим 2 * mainValue штук рыб в другой пустой бассейн')
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day, koef, deltaMass)
        self.print_info()
        currentIndex += 1

        # вырастим рыбу в 1 бассейне
        print('вырастим рыбу в 1 бассейне')
        day = self.grow_up_fish_in_one_pool(day, startDateSaving)
        print(day)
        self.print_info()

        return [mainValue, day, currentIndex]

    def main_work_with_print(self, startDate, endDate, masses, reserve, deltaMass):
        resultStartScript = self.start_script_with_print(masses, reserve, startDate, self.correctionFactor, deltaMass)

        day = resultStartScript[1]
        # [mainVolumeFish, day, currentIndex]
        resultMainScript = self.main_script_with_print(resultStartScript[0],
                                             resultStartScript[1],
                                             resultStartScript[2],
                                             startDate, self.correctionFactor, deltaMass)

        numberMainScript = 2
        while (day < endDate):
            numberMainScript += 1
            # [mainValue, day, currentIndex]
            resultMainScript = self.main_script_with_print(resultMainScript[0],
                                                 resultMainScript[1],
                                                 resultMainScript[2],
                                                 startDate, self.correctionFactor, deltaMass)
            day = resultMainScript[1]


class CWSD():
    amountModules = 0
    amountPools = 0
    modules = list()
    square = 0
    salary = 0
    amountWorkers = 0
    equipmentCapacity = 0.0
    rent = 0
    costElectricity = 0
    costCWSD = 0
    masses = 0
    feedPrice = 0
    depreciationReservePercent = 0.0
    expansionReservePercent = 0.0
    depreciationReserve = 0
    expansionReserve = 0
    principalDebt = 0
    annualPercentage = 0
    amountMonth = 0
    grant = 0

    feedings = list()
    fries = list()
    salaries = list()
    rents = list()
    electricities = list()
    revenues = list()
    resultBusinessPlan = list()

    monthlyPayment = 0



    def __init__(self, masses, amountModules=2, amountPools=4, square=10,
                 correctionFactor=2,feedPrice=260, salary=30000,
                 amountWorkers=2, equipmentCapacity=5.5, costElectricity=3.17, rent=70000,
                 costCWSD=0, depreciationReservePercent=10.0, expansionReservePercent=10.0,
                 principalDebt=450000, annualPercentage=15, amountMonth=12, grant=4500000):
        self.amountModules = amountModules
        self.feedPrice = feedPrice
        self.modules = list()
        for i in range(amountModules):
            module = Module(square, masses, amountPools, correctionFactor)
            self.modules.append(module)

        self.masses = masses
        self.amountPools = amountPools
        self.salary = salary
        self.amountWorkers = amountWorkers
        self.equipmentCapacity = equipmentCapacity
        self.costElectricity = costElectricity
        self.rent = rent
        self.costCWSD = costCWSD
        self.depreciationReservePercent = depreciationReservePercent
        self.expansionReservePercent = expansionReservePercent
        self.depreciationReserve = 0
        self.expansionReserve = 0
        self.principalDebt = principalDebt
        self.annualPercentage = annualPercentage
        self.amountMonth = amountMonth
        self.grant = grant

        self.feedings = list()
        self.fries = list()
        self.salaries = list()
        self.rents = list()
        self.electricities = list()
        self.revenues = list()
        self.resultBusinessPlan = list()

    def _calculate_all_casts_and_profits_for_all_period(self, startDate, endDate):
        for i in range(self.amountModules):
            for j in range(self.amountPools):
                for k in range(len(self.modules[i].pools[j].feeding)):
                    # [day, todayFeedMass]
                    self.feedings.append([self.modules[i].pools[j].feeding[k][0],
                                          self.modules[i].pools[j].feeding[k][1] * self.feedPrice])
                for k in range(len(self.modules[i].pools[j].arrayFryPurchases)):
                    # [date, amountFishes, averageMass, totalPrice]
                    self.fries.append([self.modules[i].pools[j].arrayFryPurchases[k][0],
                                      self.modules[i].pools[j].arrayFryPurchases[k][3]])
                for k in range(len(self.modules[i].pools[j].arraySoldFish)):
                    # [day, amountSoldFish, soldBiomass, revenue]
                    self.revenues.append([self.modules[i].pools[j].arraySoldFish[k][0],
                                          self.modules[i].pools[j].arraySoldFish[k][3]])

        startMonth = startDate
        endMonth = calculate_end_date_of_month(startMonth) - date.timedelta(1)
        while (endMonth <= endDate):
            self.rents.append([endMonth, self.rent])
            self.salaries.append([endMonth, self.amountWorkers * self.salary])
            amountDaysInThisMonth = (endMonth - startMonth).days
            self.electricities.append([endMonth,
                                      amountDaysInThisMonth * 24 * self.equipmentCapacity * self.costElectricity])
            startMonth = endMonth + date.timedelta(1)
            endMonth = calculate_end_date_of_month(startMonth) - date.timedelta(1)

    def work_cwsd(self, startDate, endDate, reserve, deltaMass):
        for i in range(self.amountModules):
            self.modules[i].main_work1(startDate, endDate, self.masses, reserve, deltaMass)

        self._calculate_all_casts_and_profits_for_all_period(startDate, endDate)

    def work_cwsd_with_print(self, startDate, endDate, reserve, deltaMass):
        for i in range(self.amountModules):
            self.modules[i].main_work_with_print(startDate, endDate, self.masses, reserve, deltaMass)

        self._calculate_all_casts_and_profits_for_all_period(startDate, endDate)

    def _find_events_in_this_period(self, array, startPeriod, endPeriod):
        result = 0
        for i in range(len(array)):
            if (startPeriod <= array[i][0] < endPeriod):
                result += array[i][1]
        return result

    def _find_event_on_this_day(self, array, day):
        result = 0
        for i in range(len(array)):
            if (array[i][0] == day):
                result += array[i][1]
        return result

    def calculate_result_business_plan(self, startDate, endDate, limitSalary):
        startMonth = startDate
        endMonth = calculate_end_date_of_month(startMonth)
        currentBudget = self.principalDebt + self.grant - self.costCWSD
        self.monthlyPayment = self.calculate_monthly_loan_payment()
        currentMonth = 1

        while(endMonth <= endDate):
            item = [endMonth, currentBudget]
            bioCost_fries = self._find_events_in_this_period(self.fries, startMonth, endMonth)
            item.append(bioCost_fries)
            bioCost_feedings = self._find_events_in_this_period(self.feedings, startMonth, endMonth)
            item.append(bioCost_feedings)
            techCost_salaries = self._find_events_in_this_period(self.salaries, startMonth, endMonth)
            item.append(techCost_salaries)
            techCost_rents = self._find_events_in_this_period(self.rents, startMonth, endMonth)
            item.append(techCost_rents)
            techCost_electricities = self._find_events_in_this_period(self.electricities, startMonth, endMonth)
            item.append(techCost_electricities)
            revenue = self._find_events_in_this_period(self.revenues, startMonth, endMonth)
            item.append(revenue)

            currentBudget += revenue - bioCost_fries - bioCost_feedings - techCost_salaries\
                             - techCost_rents - techCost_electricities

            if (currentMonth <= self.amountMonth):
                currentBudget -= self.monthlyPayment
                currentMonth += 1
            else:
                self.monthlyPayment = 0


            if ((startDate.day == endMonth.day) and
                    (startDate.month == endMonth.month) and
                    (startDate.year != endMonth.year) and
                    (currentBudget > 0)):
                currentDepreciationReserve = currentBudget * self.depreciationReservePercent / 100
                self.depreciationReserve += currentDepreciationReserve
                currentExpansionReserve = currentBudget * self.expansionReservePercent / 100
                self.expansionReserve += currentExpansionReserve
            else:
                currentDepreciationReserve = 0
                currentExpansionReserve = 0

            item.append(currentBudget)
            item.append(self.depreciationReserve)
            item.append(self.expansionReserve)
            item.append(self.monthlyPayment)
            item.append(currentDepreciationReserve + currentExpansionReserve + self.monthlyPayment +
                        techCost_electricities + techCost_rents + techCost_salaries + bioCost_feedings +
                        bioCost_fries
                        )

            # item = [конец этого месяца, предыдущий бюджет, траты на мальков,
            #         на корм, на зарплату, на аренду, на электричество, выручка, текущий бюджет,
            #         резерв на амортизацию, резерв на расширение, месячная плата за кредит, общие расходы]
            self.resultBusinessPlan.append(item)
            startMonth = endMonth
            endMonth = calculate_end_date_of_month(startMonth)

        self.calculate_family_profit(limitSalary)

        return self.resultBusinessPlan[len(self.resultBusinessPlan) - 1][8]

    def find_minimal_budget(self):
        # item = [конец этого месяца, предыдущий бюджет, траты на мальков,
        #         на корм, на зарплату, на аренду, на электричество, выручка, текущий бюджет,
        #         резерв на амортизацию, резерв на расширение]
        result = self.resultBusinessPlan[0][8]
        for i in range(len(self.resultBusinessPlan)):
            if (result > self.resultBusinessPlan[i][8]):
                result = self.resultBusinessPlan[i][8]
        return result

    def print_info(self, startDate):
        startMonth = startDate

        for i in range(len(self.resultBusinessPlan)):
            item = self.resultBusinessPlan[i]
            # item = [конец этого месяца, предыдущий бюджет, траты на мальков,
            #         на корм, на зарплату, на аренду, на электричество, выручка, текущий бюджет,
            #         резерв на амортизацию оборудования, резерв на расширение]
            print('------------------------------------------------------------')
            print(i, ' месяц, с ', startMonth, ' по ', item[0])
            print('На конец текущего месяца ситуация в бассейнах будет следующая:')
            for j in range(self.amountModules):
                for k in range(self.amountPools):
                    # [день, количество рыбы, биомасса, средняя масса, плотность]
                    print(j * self.amountPools + k, ' бассейн, количество мальков: ',
                          self.modules[j].pools[k].poolHistory[i][1], ' биомасса: ',
                          self.modules[j].pools[k].poolHistory[i][2], ' средняя масса: ',
                          self.modules[j].pools[k].poolHistory[i][3], ' плотность посадки: ',
                          self.modules[j].pools[k].poolHistory[i][4])
            print('Бюджет с прошлого месяца: ', item[1])
            print('Будет затрачено на мальков: ', item[2])
            print('На корм: ', item[3])
            print('На зарплату: ', item[4])
            print('На аренду: ', item[5])
            print('На электричество: ', item[6])
            print('Выплаты за кредит: ', item[11])
            if (i != len(self.resultBusinessPlan) - 1):
                print('Зарплата семье: ', item[13])
            print('Общие расходы: ', item[12])
            print('Резерв на амортизацию оборудования составляет: ', item[9])
            print('Резерв на расширение производства составляет: ', item[10])
            print('Выручка составит: ', item[7])
            print('Бюджет на конец текущего месяца месяца составит: ', item[8])
            print()
            startMonth = item[0]

    def calculate_monthly_loan_payment(self):
        monthlyPercentage = self.annualPercentage / 12 / 100
        annuityRatio = monthlyPercentage * (1 + monthlyPercentage) ** self.amountMonth
        annuityRatio /= (1 + monthlyPercentage) ** self.amountMonth - 1
        monthlyPayment = self.principalDebt * annuityRatio
        return monthlyPayment

    def calculate_family_profit(self, limitSalary):
        for i in range(len(self.resultBusinessPlan) - 1):
            currentBusinessInfo = self.resultBusinessPlan[i]
            nextBusinessInfo = self.resultBusinessPlan[i + 1]
            delta = currentBusinessInfo[7] - nextBusinessInfo[12]
            # item = [конец этого месяца, предыдущий бюджет, траты на мальков,
            #         на корм, на зарплату, на аренду, на электричество, выручка, текущий бюджет,
            #         резерв на амортизацию, резерв на расширение, месячная плата за кредит, общие расходы]
            ourSalary = 0
            if (currentBusinessInfo[8] > 0):
                if (delta > 2 * limitSalary):
                    ourSalary = 2 * limitSalary
                elif (0 < delta <= 2 * limitSalary):
                    ourSalary = delta / 2
                else:
                    ourSalary = 0
            self.resultBusinessPlan[i][8] -= ourSalary
            self.resultBusinessPlan[i][12] += ourSalary
            self.resultBusinessPlan[i].append(ourSalary)


class Business():
    cwsds = list()
    amountCWSDs = 0
    startMasses = list()
    totalBudget = 0

    def __init__(self, startMasses):
        self.cwsds = list()
        self.startMasses = startMasses
        amountCWSDs = 1

        newCWSD = CWSD(startMasses, 2, 4, 10, 2, 260, 40000, 2, 5.5, 3.17,
                       100000, 3000000, 7.5, 7.5, 500000, 15, 36, 5000000)
        self.cwsds.append(newCWSD)

        self.totalBudget = 0

    def addNewCWSD(self):
        newCWSD = CWSD(self.startMasses, 2, 4, 10, 2, 260, 40000, 2, 5.5, 3.17,
                       100000, 3000000, 7.5, 7.5, 500000, 15, 36, 5000000)
        self.cwsds.append(newCWSD)



'''
masses = [100, 70, 50, 20]
cwsd = Module(20, masses, 30000, 2, 4, 4, 1000, 200, 5.5, 70000, 3.17, 21, 5, 0)

cwsd.main_work1(date.date.today(), date.date(2028, 1, 1), masses, 20)
cwsd.show_all_information_every_month(date.date.today(), date.date(2028, 1, 1))
'''
'''
masses = [100, 50, 30, 20]
# masses, amountModules=2, amountPools=4, square=10, correctionFactor=2,feedPrice=260, salary=30000,
#                  amountWorkers=2, equipmentCapacity=5.5, costElectricity=3.17, rent=70000,
#                  costCWSD=0, depreciationReservePercent=10, expansionReservePercent=10
cwsd = CWSD(masses, 2, 4, 10, 2, 260, 40000, 2, 5.5, 3.17, 70000, 3000000, 10, 18)
cwsd.work_cwsd(date.date.today(), date.date(2028, 1, 1), 50, 50)
cwsd.calculate_result_business_plan(date.date.today(), date.date(2028, 1, 1))
cwsd.print_info(date.date.today())
'''
# arrayFryPurchases[i] = [date, amountFries, averageMass, totalPrice]
# costFishFry = [[5, 35], [10, 40], [20, 45], [30, 50], [50, 60], [100, 130]]
'''
x = Opimization()
masses = [100, 50, 30, 20]
result = x.calculate_optimal_deltaMass(masses, 10, 10, 300, date.date.today(), date.date(2028, 1, 1))
print(result)
print()
print()
print()
print()
print()
print('Начата проверка!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
print()
print()
print()
print()
print()
'''
masses = [100, 50, 30, 20]

cwsd = CWSD(masses, 2, 4, 10, 2, 260, 40000, 2, 5.5, 3.17, 100000, 3000000, 7.5, 7.5, 500000, 15, 36, 5000000)
cwsd.work_cwsd_with_print(date.date.today(), date.date(2028, 1, 1), 50, 50)
cwsd.calculate_result_business_plan(date.date.today(), date.date(2028, 1, 1), 100000)
cwsd.print_info(date.date.today())
print(cwsd.find_minimal_budget())